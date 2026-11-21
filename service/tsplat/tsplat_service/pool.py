"""Registry pool worker: runs the asset registry's `image-to-splat` transforms on this TripoSplat (task 1411).

The registry owns sign-in (its SSO), groups and permissions: a person runs `image-to-splat` on an image in one of
their groups, and the output lands in that group as a `splat-ply`, chained to `ply-to-dgs` -> bundle. This worker only
sees jobs: it claims one with the pool's bearer, reads the input from the presigned URL it is given, and hands the PLY
back through a presigned PUT. It holds no S3 keys and never touches group content directly (registry docs, splat_pool).
"""
import hashlib, json, logging, os, shutil, threading, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

from . import registry, worker

log = logging.getLogger("tsplat.pool")
STATE = {"enabled": False, "last_claim": None, "last_job": None, "errors": 0}
POOL = None                                                    # the running Pool, so shutdown can requeue its job


def requeue_on_exit():
    """SIGTERM mid-job: hand the registry job back so it runs again, instead of leaving it claimed."""
    if POOL and POOL.current:
        POOL.requeue(POOL.current); log.info("requeued registry job %s on shutdown", POOL.current)


class Pool:
    def __init__(self, cfg, warm):
        c = cfg["registry_pool"]
        self.base = c["url"].rstrip("/"); self.name = c["pool"]; self.presets = ",".join(c.get("presets", ["image-to-splat"]))
        self.token_file = Path(c["token_file"]).expanduser(); self.poll_s = c.get("poll_s", 10)
        self.host = c.get("worker", "tsplat-obelisk"); self.warm = warm
        self.worker_name = f"{self.host}:{os.getpid()}"           # host:pid, so a restart can find what a dead run held
        self.work_root = Path(cfg["state_dir"]).expanduser() / "pool-work"
        self.current = None

    def _hdr(self):
        t = self.token_file.read_text().strip()
        if t.lower().startswith("authorization:"): t = t.split(":", 1)[1].strip()
        return t if t.startswith("Bearer ") else f"Bearer {t}"

    def call(self, method, path, body=None):
        r = urllib.request.Request(self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                   headers={"Authorization": self._hdr(), "Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=60) as resp:
            b = resp.read(); return json.loads(b) if b else None

    def claim(self):
        q = f"worker={urllib.parse.quote(self.worker_name)}&presets={self.presets}"
        return (self.call("POST", f"/api/pools/{self.name}/claim?{q}") or {}).get("job")

    def recover(self):
        """On start: this host's `running` jobs belong to a process that is gone, so put them back (task 1123's pattern)."""
        rows = self.call("GET", f"/api/pools/{self.name}/running?host={urllib.parse.quote(self.host)}")["items"]
        for row in rows:
            self.requeue(row["id"]); log.info("requeued %s left running by %s", row["id"], row["worker"])
        return [r["id"] for r in rows]

    def requeue(self, tid):
        try:
            self.call("POST", f"/api/pools/{self.name}/jobs/{tid}/requeue")
        except Exception as e:
            log.warning("requeue of %s failed: %s", tid, e)

    def run_job(self, job):
        """One claimed transform, with warm.gpu held and the lease granted: input -> TripoSplat -> PLY -> /complete or /fail."""
        tid = job["id"]; work = self.work_root / tid; work.mkdir(parents=True, exist_ok=True); timings = {}
        self.current = tid
        try:
            files = job["input_assets"][0]["files"]
            f = next((x for x in files if x["role"] == "source"), files[0])   # fetched first: the URL lives 900 s
            ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get((f.get("mime") or "").lower(),
                                                                                       Path(f.get("storage_key", "")).suffix or ".png")
            src = work / f"input{ext}"
            with urllib.request.urlopen(f["url"], timeout=120) as resp:   # presigned GET: no bearer
                src.write_bytes(resp.read())
            if f.get("sha256") and hashlib.sha256(src.read_bytes()).hexdigest() != f["sha256"]:
                raise RuntimeError("input sha256 does not match the registry's record")
            matte = (job.get("params") or {}).get("matte", "auto")
            if matte not in ("auto", "opaque", "rgba"): raise ValueError(f"matte {matte!r}: use auto, opaque or rgba")
            g, prepared, used = self.warm.splat(src, matte, 262144, work, timings)
            ply = work / "splat.ply"; g.save_ply(str(ply))
            frame = registry.measure(ply)
            up = self.call("POST", f"/api/pools/{self.name}/jobs/{tid}/upload", {"name": "splat.ply", "mime": "application/octet-stream"})
            raw = ply.read_bytes()
            put = urllib.request.Request(up["url"], data=raw, method="PUT", headers={"Content-Type": "application/octet-stream"})
            with urllib.request.urlopen(put, timeout=300): pass
            self.call("POST", f"/api/pools/{self.name}/jobs/{tid}/complete", {"outputs": [{
                "storage_key": up["storage_key"], "name": "splat.ply", "role": "main", "mime": "application/octet-stream",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "meta": {"splatFrame": frame, "source": "tsplat-service", "matte_used": used, "num_gaussians": 262144,
                         "timings": timings}}]})
            log.info("pool job %s done: matte %s, splat %ss", tid, used, timings.get("splat_s"))
            STATE["last_job"] = {"id": tid, "state": "completed", "at": time.time()}
        except Exception as e:
            log.error("pool job %s failed: %s", tid, e)
            STATE["last_job"] = {"id": tid, "state": "failed", "at": time.time()}
            try:
                self.call("POST", f"/api/pools/{self.name}/jobs/{tid}/fail", {"error": f"{type(e).__name__}: {e}"[:3900]})
            except Exception as e2:
                log.error("could not report failure of %s: %s", tid, e2)
        finally:
            self.current = None
            shutil.rmtree(work, ignore_errors=True)

    def step(self):
        """One poll. A registry job is only held while we can run it: if the model isn't warm or the GPU is busy, the
        probe's job goes straight back (requeue is not a failure), we wait for gpu-0 without holding it, then claim again.
        gpu-0 can queue for a long time (1,195 s and a 5.5 h stall on 21 Nov). Returns True if a job ran."""
        job = self.claim(); STATE["last_claim"] = time.time()
        if not job: return False
        if self.warm.pipe and self.warm.gpu.acquire(blocking=False):
            try:
                self.run_job(job); return True
            finally:
                self.warm.gpu.release()
        self.requeue(job["id"])
        with self.warm.gpu:
            self.warm.ensure()                                   # may wait in gpu-0's queue; nothing claimed meanwhile
            self.warm.last_used = time.time()
            job = self.claim()
            if not job: return False                             # taken or cancelled; the idle path drops the lease
            self.run_job(job); return True

    def loop(self):
        STATE["enabled"] = True
        try:
            self.recover()
        except Exception as e:
            log.warning("pool recovery failed: %s", e)
        while True:
            try:
                if self.step(): continue                         # look again straight away
            except Exception as e:                               # registry down, token wrong, lease failed: back off
                STATE["errors"] += 1; log.warning("pool step failed: %s", e)
                time.sleep(min(300, self.poll_s * 6)); continue
            time.sleep(self.poll_s)


def start(cfg):
    c = cfg.get("registry_pool")
    if not c: return None
    if not Path(c["token_file"]).expanduser().exists():
        log.warning("registry pool configured but %s is missing; pool off", c["token_file"]); return None
    while worker.WARM is None: time.sleep(0.05)              # the worker thread creates the shared Warm
    global POOL
    p = POOL = Pool(cfg, worker.WARM)
    threading.Thread(target=p.loop, daemon=True, name="registry-pool").start()
    log.info("registry pool %s at %s", p.name, p.base)
    return p
