"""The single worker: holds the GPU lease and a warm TripoSplat pipeline while there is work, releases both when idle."""
import json, logging, os, queue, shutil, sys, threading, time, traceback
from pathlib import Path

from . import plane, registry, render

log = logging.getLogger("tsplat.worker")
BEARERS = {}                                   # job id -> caller bearer, memory only
STATE = {"loaded": False, "lease": None}


def _torch():
    try:
        import torch
        return torch
    except ImportError:
        return None


def _mps(torch):
    return torch is not None and torch.backends.mps.is_available()


class Warm:
    """Lease + pipeline, acquired on first job and released after cfg idle_release_s without work."""

    def __init__(self, cfg, me):
        self.cfg, self.me = cfg, me
        self.pipe = None; self.lease = None; self.stop = threading.Event(); self.lease_wait_s = 0.0

    def ensure(self):
        if self.pipe: return self.pipe
        try:
            return self._acquire_and_load()
        except BaseException:                      # a failed wait, import or load must not leave a lease behind:
            log.error("acquire/load failed; giving back lease %s", self.lease)   # gpu-0 is expiry_policy hold
            self.release()
            raise

    def _acquire_and_load(self):
        t = time.time()
        def held(lid):                             # known while still queued, so shutdown can withdraw it
            self.lease = lid; STATE["lease"] = lid
        self.lease = self.me.lease_acquire(on_id=held); STATE["lease"] = self.lease
        self.lease_wait_s = round(time.time() - t, 1)
        self.stop.clear()
        threading.Thread(target=self._renew, daemon=True, name="renew").start()
        repo = Path(self.cfg["triposplat_repo"]).expanduser()
        sys.path.insert(0, str(repo))
        import torch
        from triposplat import TripoSplatPipeline
        ck = repo / "ckpts"
        t = time.time()
        self.pipe = TripoSplatPipeline(
            ckpt_path=str(ck / "diffusion_models/triposplat_fp16.safetensors"),
            decoder_path=str(ck / "vae/triposplat_vae_decoder_fp16.safetensors"),
            dinov3_path=str(ck / "clip_vision/dino_v3_vit_h.safetensors"),
            flux2_vae_encoder_path=str(ck / "vae/flux2-vae.safetensors"),
            rmbg_path=str(ck / "background_removal/birefnet.safetensors"),
            device="mps" if torch.backends.mps.is_available() else "cpu")
        STATE["loaded"] = True
        log.info("pipeline loaded in %.1fs under lease %s", time.time() - t, self.lease)
        return self.pipe

    def _renew(self):
        every = self.cfg.get("renewal_interval", 30)
        while not self.stop.wait(every):
            try:
                self.me.lease_renew(self.lease)
            except Exception as e:                 # a lost lease means unload now, not keep running unclaimed
                log.error("lease renew failed (%s); unloading", e); self.release(); return

    def release(self):
        self.stop.set()
        if self.pipe is not None:
            self.pipe = None
            import gc
            gc.collect()
            torch = _torch()
            if _mps(torch): torch.mps.empty_cache()
        STATE["loaded"] = False
        if self.lease:
            self.me.lease_release(self.lease); log.info("released lease %s", self.lease)
        self.lease = None; STATE["lease"] = None


def splat_one(pipe, src: Path, matte: str, n: int, work: Path):
    """Run TripoSplat; `auto` falls back to the whole frame when BiRefNet finds no subject (task 1399)."""
    from PIL import Image
    used = matte
    if matte == "opaque":
        src = _opaque(src, work)
    elif matte == "rgba":
        im = Image.open(src)
        if im.mode != "RGBA" or min(im.getchannel("A").getextrema()) == 255:
            raise ValueError("matte=rgba needs an image with a real alpha channel")
    try:
        g, prepared = pipe.run(str(src), num_gaussians=n, show_progress=False)
    except ValueError as e:
        if matte != "auto" or "zero-size array" not in str(e): raise
        used = "auto→opaque (empty matte)"
        g, prepared = pipe.run(str(_opaque(src, work)), num_gaussians=n, show_progress=False)
    return g, prepared, used


def _opaque(src: Path, work: Path):
    from PIL import Image
    im = Image.open(src).convert("RGBA")
    im.putpixel((0, 0), im.getpixel((0, 0))[:3] + (254,))  # min alpha < 255 makes TripoSplat skip BiRefNet
    out = work / "opaque.png"; im.save(out); return out


WARM = None                                    # the live Warm, so shutdown can release its lease


def release_on_exit():
    """Give the gpu-0 lease back when the process is stopped (launchctl bootout sends SIGTERM)."""
    w = WARM
    if w and w.lease:
        w.stop.set()
        w.me.lease_release(w.lease); log.info("released lease %s on shutdown", w.lease)
        w.lease = None; STATE["lease"] = None


def run(cfg, jobs, me):
    global WARM
    warm = WARM = Warm(cfg, me)
    api = cfg["plane_url"]; idle = cfg.get("idle_release_s", 600)
    sink = cfg.get("file_group")
    reg = registry.Registry(cfg, me) if cfg.get("publish_enabled") else None
    while True:
        try:
            jid = jobs.q.get(timeout=idle)
        except queue.Empty:
            if warm.pipe or warm.lease: log.info("idle %ss; releasing", idle); warm.release()
            continue
        j = jobs.get(jid)
        if not j or j["state"] not in ("queued",): continue
        bearer = BEARERS.pop(jid, None)
        work = Path(cfg["state_dir"]).expanduser() / "work" / jid
        work.mkdir(parents=True, exist_ok=True)
        t0 = time.time(); timings = {}
        try:
            if bearer is None:
                raise RuntimeError("the caller's credential was lost (service restarted); resubmit")
            jobs.update(jid, state="running", started_at=t0)
            spec = j["spec"]
            src = plane.fetch_as_caller(api, bearer, spec["file_id"], work / "input.png")
            timings["fetch_s"] = round(time.time() - t0, 1)
            warm.lease_wait_s = 0.0
            t = time.time(); pipe = warm.ensure()
            timings["lease_wait_s"] = warm.lease_wait_s                      # queued behind other gpu-0 holders
            timings["load_s"] = round(time.time() - t - warm.lease_wait_s, 1)
            torch = _torch()
            t = time.time()
            g, prepared, used = splat_one(pipe, src, spec["matte"], spec["num_gaussians"], work)
            timings["splat_s"] = round(time.time() - t, 1)
            if _mps(torch):
                timings["peak_mps_gb"] = round(torch.mps.driver_allocated_memory() / 2**30, 1)
            stem = f"tsplat-{spec['file_id']}"
            ply = work / f"{stem}.ply"; g.save_ply(str(ply))
            prep = work / f"{stem}-prepared.webp"; prepared.save(str(prep))
            result = {"matte_used": used, "num_gaussians": spec["num_gaussians"],
                      "frame": {"up": [0, -1, 0], "view": [-1, 0, 0]},
                      "ply_file_id": me.upload(ply, sink), "prepared_file_id": me.upload(prep, sink)}
            if spec["render"]:
                t = time.time()
                beauty, sheet = render.beauty(ply, work), render.sheet(ply, work)
                result["beauty_file_id"] = me.upload(beauty, sink); result["sheet_file_id"] = me.upload(sheet, sink)
                timings["render_s"] = round(time.time() - t, 1)
            if spec.get("publish") is not None:      # quick part now; the bundle is followed off the GPU worker
                t = time.time()
                name = spec["publish"].get("name") or f"tsplat {spec['file_id']} ({j['requester']}, job {jid})"
                try:                                 # a registry failure must not cost the caller their splat
                    result["registry"] = reg.start(ply, name)
                except Exception as e:
                    log.warning("publish start failed for %s: %s", jid, e)
                    result["registry"] = {"state": "failed", "error": f"{type(e).__name__}: {e}"}
                timings["publish_start_s"] = round(time.time() - t, 1)
            # Hosted delivery: outputs live in the sink group, so each is linked to reply_to and the link read back.
            # Readers of that object can then read the files. All of it happens before the job reads as done.
            r = spec["reply_to"]
            result["links"] = {k: me.link(result[k], r["kind"], r["id"])
                               for k in ("ply_file_id", "prepared_file_id", "beauty_file_id", "sheet_file_id") if k in result}
            timings["total_s"] = round(time.time() - t0, 1)
            body = (f"tsplat-service job `{jid}` for {j['requester']}: file {spec['file_id']} → "
                    f"[PLY](/api/v1/files/{result['ply_file_id']}/raw) ({spec['num_gaussians']} Gaussians, matte {used}, "
                    f"{timings['splat_s']} s).")
            if "beauty_file_id" in result:
                body += f"\n\n![](/api/v1/files/{result['beauty_file_id']}/raw)"
            reg_state = result.get("registry", {}).get("state")
            if reg_state == "converting":
                body += "\n\nRegistry publish to *tsplat drafts* is converting; the bundle id follows here."
            elif reg_state == "failed":
                body += f"\n\nRegistry publish failed: {result['registry']['error'][:300]}"
            try:
                me.comment(r["kind"], r["id"], body); result["reply_to_posted"] = True
            except Exception as e:                     # the links are the delivery; the comment is a courtesy
                log.warning("reply_to comment failed: %s", e); result["reply_to_posted"] = False
            jobs.update(jid, state="done", result=result, timings=timings, finished_at=time.time())
            if result.get("registry", {}).get("state") == "converting":
                registry.follow(reg, jobs, me, jid, result["registry"], r)
        except Exception as e:
            log.error("job %s failed: %s", jid, e); log.debug(traceback.format_exc())
            jobs.update(jid, state="failed", error=f"{type(e).__name__}: {e}", timings=timings, finished_at=time.time())
        finally:
            shutil.rmtree(work, ignore_errors=True)
