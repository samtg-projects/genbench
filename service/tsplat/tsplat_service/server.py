"""tsplat-service: TripoSplat image -> 3D Gaussian splat PLY, as an authenticated async network service.

Design: samcloud doc 683 (task 1401). Pattern follows obelisk-services/image-service:
every route needs a samcloud bearer (verified per call), jobs are async with an idempotency key,
inputs are fetched with the *caller's* bearer, outputs are uploaded under the service identity.
"""
import hashlib, json, logging, os, queue, signal, sys, threading, time, urllib.error, urllib.parse, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import plane, worker

UI_HTML = (Path(__file__).parent / "ui.html").read_bytes()
SAFE_IMAGES = ("image/png", "image/jpeg", "image/webp")      # never text/html or image/svg+xml from this origin

log = logging.getLogger("tsplat")


class Jobs:
    """In-memory job table persisted to state_dir/jobs.json, keyed by job id and (requester, idempotency key)."""

    def __init__(self, state_dir: Path):
        self.path = state_dir / "jobs.json"
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        self.jobs = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.q = queue.Queue()
        for j in self.jobs.values():                       # requeue work interrupted by a restart
            if j["state"] in ("queued", "running"):
                j["state"] = "queued"; self.q.put(j["id"])

    def _save(self):
        tmp = self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(self.jobs)); tmp.replace(self.path)

    def submit(self, requester, idem, spec, bearer_ref):
        with self.lock:
            for j in self.jobs.values():               # a key whose job failed may start a fresh one
                if j["requester"] == requester and j["idempotency_key"] == idem and j["state"] != "failed":
                    return j, False
            jid = "tsj_" + uuid.uuid4().hex[:16]
            j = {"id": jid, "requester": requester, "idempotency_key": idem, "spec": spec, "state": "queued",
                 "created_at": time.time(), "result": None, "error": None, "timings": {}}
            self.jobs[jid] = j; self._save()
        worker.BEARERS[jid] = bearer_ref                  # caller bearer, memory only, dropped when the job ends
        self.q.put(jid)
        return j, True

    def update(self, jid, **kw):
        with self.cv:
            self.jobs[jid].update(kw); self._save(); self.cv.notify_all()

    def get(self, jid):
        with self.lock:
            j = self.jobs.get(jid)
            return json.loads(json.dumps(j)) if j else None

    def wait(self, jid, timeout_s):
        end = time.time() + timeout_s
        with self.cv:
            while self.jobs.get(jid, {}).get("state") in ("queued", "running") and time.time() < end:
                self.cv.wait(max(0.1, end - time.time()))
        return self.get(jid)

    def result_file_ids(self, requester):
        """File ids in this requester's own job results: the only ones the result viewer will proxy."""
        keys = ("ply_file_id", "prepared_file_id", "beauty_file_id", "sheet_file_id")
        with self.lock:
            return {j["result"][k] for j in self.jobs.values() if j["requester"] == requester and j.get("result")
                    for k in keys if k in j["result"]}

    def depth(self):
        with self.lock:
            return sum(1 for j in self.jobs.values() if j["state"] in ("queued", "running"))


def public(j):
    return {k: j[k] for k in ("id", "requester", "state", "created_at", "result", "error", "timings", "spec")}


MATTES = ("auto", "opaque", "rgba")


def validate(body):
    if not isinstance(body, dict): raise ValueError("body must be a JSON object")
    fid = body.get("file_id")
    if not isinstance(fid, int) or fid <= 0: raise ValueError("file_id must be a positive integer")
    matte = body.get("matte", "auto")
    if matte not in MATTES: raise ValueError(f"matte must be one of {MATTES}")
    n = body.get("num_gaussians", 262144)
    if not isinstance(n, int) or not 16384 <= n <= 262144: raise ValueError("num_gaussians must be 16384..262144")
    reply_to = body.get("reply_to")              # required: outputs are delivered by linking them to it
    if not (isinstance(reply_to, dict) and reply_to.get("kind") in ("task", "ticket") and isinstance(reply_to.get("id"), int)):
        raise ValueError("reply_to {kind: task|ticket, id: int} is required for hosted delivery")
    publish = body.get("publish")
    if publish is not None and not (isinstance(publish, dict) and set(publish) <= {"name"}
                                    and isinstance(publish.get("name", ""), str) and len(publish.get("name", "")) <= 120):
        raise ValueError("publish must be {} or {name: str (<=120)}")
    return {"file_id": fid, "matte": matte, "num_gaussians": n, "reply_to": reply_to,
            "render": bool(body.get("render", True)), "publish": publish}


def make_handler(cfg, jobs, auth, me):
    class H(BaseHTTPRequestHandler):
        server_version = "tsplat-service"

        def log_message(self, *a):                     # no paths, tokens or bodies in shared logs
            pass

        def _send(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def _auth(self):
            bearer = self.headers.get("Authorization", "")
            who = auth.verify(bearer)
            if who is None:
                self._send(401, {"error": "a valid samcloud bearer is required"}); return None, None
            if not (set(who["groups"]) & set(cfg["allowed_groups"]) or who["username"] in cfg.get("allowed_users", [])):
                self._send(403, {"error": "not in an allowed group"}); return None, None
            return who, bearer

        def _bytes(self, code, data, ctype, attachment=None):
            self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data)))
            if attachment: self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
            self.send_header("Cache-Control", "no-store"); self.send_header("X-Content-Type-Options", "nosniff")
            if ctype.startswith("text/html"):
                self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; "
                                                          "script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(data)

        def do_GET(self):
            p = self.path.split("?")[0].rstrip("/")
            if p in ("", "/ui"):                           # the test page: static, holds no data; every call it makes is authenticated
                return self._bytes(200, UI_HTML, "text/html; charset=utf-8")
            who, bearer = self._auth()
            if not who: return
            if p.startswith("/v1/files/") and p.endswith("/raw"):
                try:
                    fid = int(p.split("/")[3])
                except ValueError:
                    return self._send(400, {"error": "bad file id"})
                if fid not in jobs.result_file_ids(who["username"]):   # only outputs of the caller's own jobs
                    return self._send(404, {"error": "not one of your job outputs"})
                try:
                    data, ctype = plane.raw_as_caller(cfg["plane_url"], bearer, fid)
                except urllib.error.HTTPError as e:
                    return self._send(e.code, {"error": "cannot read that file"})
                ctype = ctype.split(";")[0].strip().lower()
                if ctype in SAFE_IMAGES:
                    return self._bytes(200, data, ctype)
                return self._bytes(200, data, "application/octet-stream", attachment=f"tsplat-{fid}.bin")
            if p == "/health":
                return self._send(200, {"status": "ok", "service": "tsplat-service", "version": cfg.get("version"),
                                        "model_loaded": worker.STATE["loaded"], "lease": worker.STATE["lease"],
                                        "queue_depth": jobs.depth()})
            if p.startswith("/v1/jobs/"):
                parts = p.split("/")
                j = jobs.get(parts[3])
                if not j or j["requester"] != who["username"] and who["username"] not in cfg.get("admins", []):
                    return self._send(404, {"error": "no such job"})
                if len(parts) == 5 and parts[4] == "wait":
                    q = dict(kv.split("=", 1) for kv in self.path.split("?", 1)[1].split("&")) if "?" in self.path else {}
                    j = jobs.wait(j["id"], min(float(q.get("timeout_s", 30)), 120))
                return self._send(200, public(j))
            self._send(404, {"error": "not found"})

        def do_POST(self):
            who, bearer = self._auth()
            if not who: return
            p = self.path.split("?")[0].rstrip("/")
            if p == "/v1/upload":                          # the test page's image upload, stored as the caller
                n = int(self.headers.get("Content-Length") or 0)
                ctype = self.headers.get("Content-Type", "")
                if ctype.split(";")[0].strip().lower() not in SAFE_IMAGES:
                    return self._send(415, {"error": "send an image (image/png, image/jpeg, image/webp)"})
                ctype = ctype.split(";")[0].strip().lower()
                if not 0 < n <= 25 * 2**20: return self._send(413, {"error": "image must be 1 byte to 25 MB"})
                q = dict(kv.split("=", 1) for kv in self.path.split("?", 1)[1].split("&")) if "?" in self.path else {}
                try:
                    fid = plane.upload_bytes(cfg["plane_url"], bearer, urllib.parse.unquote(q.get("name", "upload.png")),
                                             self.rfile.read(n), ctype, "work")
                except urllib.error.HTTPError as e:
                    if e.code == 403:
                        return self._send(403, {"error": "uploads go to the work group, and you are not in it; give an existing file id instead"})
                    return self._send(e.code, {"error": "the files plane refused the upload"})
                return self._send(201, {"file_id": fid})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n > 65536: return self._send(413, {"error": "body too large"})
                body = json.loads(self.rfile.read(n) or b"{}")
            except (ValueError, json.JSONDecodeError):
                return self._send(400, {"error": "invalid JSON"})
            if p == "/v1/splat":
                idem = self.headers.get("Idempotency-Key") or hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:32]
                try:
                    spec = validate(body)
                except ValueError as e:
                    return self._send(400, {"error": str(e)})
                if spec["publish"] is not None and not cfg.get("publish_enabled"):
                    return self._send(400, {"error": "publish is not enabled on this deployment yet"})
                r = spec["reply_to"]                    # checked now, before any GPU work
                if not plane.caller_can_read(cfg["plane_url"], bearer, r["kind"], r["id"]):
                    return self._send(403, {"error": f"you cannot read {r['kind']} {r['id']}"})
                if not me.can_read(r["kind"], r["id"]):
                    return self._send(403, {"error": f"the service cannot read {r['kind']} {r['id']}; pick an object in work or projects"})
                j, new = jobs.submit(who["username"], idem, spec, bearer)
                return self._send(202 if new else 200, public(j))
            self._send(404, {"error": "not found"})

    return H


def main():
    cfg = json.loads(Path(sys.argv[sys.argv.index("--config") + 1]).read_text())
    state = Path(cfg["state_dir"]).expanduser(); state.mkdir(parents=True, exist_ok=True); os.chmod(state, 0o700)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    me = plane.Principal(cfg)
    me.check()                                          # refuses to start under the wrong identity
    jobs = Jobs(state)
    threading.Thread(target=worker.run, args=(cfg, jobs, me), daemon=True, name="worker").start()
    srv = ThreadingHTTPServer((cfg.get("host", "127.0.0.1"), int(cfg["port"])), make_handler(cfg, jobs, plane.Auth(cfg), me))
    def stop(signum, _frame):
        log.info("signal %s: shutting down", signum)
        worker.release_on_exit()
        os._exit(0)
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    log.info("listening on %s:%s as %s", cfg.get("host", "127.0.0.1"), cfg["port"], me.username)
    srv.serve_forever()


if __name__ == "__main__":
    main()
