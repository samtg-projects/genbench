"""Publish a TripoSplat PLY to the immersive asset registry as a draft headset bundle.

The service's registry access is scoped by the registry itself to one group (`registry_group`), so whatever a
caller asks for, drafts land there; promoting one to a real collection is a person's call.
Path: upload the PLY -> splat-ply asset -> ply-to-dgs (chains to dgs-to-bundle) -> PATCH the bundle's
splatFrame view to -1,0,0, because the registry's measure always picks the horizontal axis nearest +z.
"""
import hashlib, json, logging, threading, time, urllib.error, urllib.request
from pathlib import Path

log = logging.getLogger("tsplat.registry")
VIEW = [-1.0, 0.0, 0.0]
UP = [0.0, -1.0, 0.0]


class Registry:
    def __init__(self, cfg, me):
        self.base = cfg["registry_url"].rstrip("/"); self.group = cfg["registry_group"]; self.me = me
        self.poll_s = cfg.get("registry_poll_s", 15); self.max_wait_s = cfg.get("registry_max_wait_s", 3600)

    def call(self, method, path, body=None, data=None, ctype="application/json"):
        if body is not None: data = json.dumps(body).encode()
        h = {"Authorization": self.me.hdr()}
        if data is not None: h["Content-Type"] = ctype
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(r, timeout=300) as resp:
                b = resp.read(); return json.loads(b) if b else None
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"registry {method} {path}: {e.code} {e.read()[:300].decode(errors='replace')}") from None

    def start(self, ply: Path, name: str):
        """The quick part, inside the job: upload, create the source asset, queue ply-to-dgs."""
        frame = measure(ply)
        raw = ply.read_bytes()
        f = self.call("POST", "/api/files", {"group_id": self.group, "name": ply.name, "mime": "application/octet-stream",
                                             "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})["file"]
        self.call("PUT", f"/api/files/{f['id']}/content", data=raw, ctype="application/octet-stream")
        src = self.call("POST", "/api/assets", {"group_id": self.group, "kind": "file", "type": "splat-ply", "name": name,
                                                "meta": {"source": "tsplat-service", "splatFrame": frame},
                                                "files": [{"file_id": f["id"], "role": "source"}]})
        t = self.call("POST", "/api/transforms", {"preset": "ply-to-dgs", "inputs": [src["id"]], "params": {"up": UP}})
        return {"state": "converting", "group_id": self.group, "source_asset": src["id"], "transform": t["id"]}

    def finish(self, reg):
        """The slow part, off the GPU worker: follow ply-to-dgs -> dgs-to-bundle, then fix the bundle's view."""
        end = time.time() + self.max_wait_s; tid = reg["transform"]; chain = [tid]
        while time.time() < end:
            t = self.call("GET", f"/api/transforms/{tid}")
            if t["status"] == "failed":
                return {**reg, "state": "failed", "error": f"{t.get('preset', 'transform')} {tid}: {str(t.get('error'))[:300]}"}
            if t["status"] == "completed":
                if t.get("preset") != "dgs-to-bundle":  # stop at the bundle; later links (splat-thumb) aren't ours
                    if not t.get("next"):
                        return {**reg, "state": "failed", "error": f"{t.get('preset')} {tid} completed with no bundle step after it"}
                    tid = t["next"]; chain.append(tid); continue
                bundle = t["outputs"][0]
                a = self.call("GET", f"/api/assets/{bundle}")
                frame = dict((a.get("meta") or {}).get("splatFrame") or {}); frame.update({"up": UP, "view": VIEW})
                self.call("PATCH", f"/api/assets/{bundle}", {"meta": {"splatFrame": frame}})
                return {**reg, "state": "published", "bundle": bundle, "transforms": chain}
            time.sleep(self.poll_s)
        return {**reg, "state": "failed", "error": f"bundle not ready after {self.max_wait_s} s (transform {tid})", "transforms": chain}


def measure(ply: Path):
    """splatFrame for a TripoSplat PLY (the registry requires up and center): median centre, and height as the
    2nd-98th percentile extent along up, so stray floaters don't stretch it."""
    import numpy as np
    from .render import _thumb
    c = _thumb()._read_ply_float_columns(ply, ["x", "y", "z"])
    xyz = np.stack([c["x"], c["y"], c["z"]], -1)
    along = xyz @ np.array(UP)
    lo, hi = np.percentile(along, [2, 98])
    return {"frame": "ply", "up": UP, "view": VIEW, "center": [round(float(v), 4) for v in np.median(xyz, 0)],
            "height": round(float(hi - lo), 4)}


def follow(registry, jobs, me, jid, reg, reply_to):
    """Run Registry.finish in its own thread and record the outcome on the job (and reply_to)."""
    def go():
        try:
            out = registry.finish(reg)
        except Exception as e:
            out = {**reg, "state": "failed", "error": f"{type(e).__name__}: {e}"}
        j = jobs.get(jid); result = dict(j["result"] or {}); result["registry"] = out
        jobs.update(jid, result=result)
        msg = (f"tsplat-service job `{jid}`: published to the registry's *{registry.group}* group as bundle `{out['bundle']}`."
               if out["state"] == "published" else f"tsplat-service job `{jid}`: registry publish failed: {out.get('error')}")
        try:
            me.comment(reply_to["kind"], reply_to["id"], msg)
        except Exception as e:
            log.warning("publish comment failed: %s", e)
    threading.Thread(target=go, daemon=True, name=f"publish-{jid}").start()
