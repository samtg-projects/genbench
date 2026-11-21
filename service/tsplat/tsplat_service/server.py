"""tsplat-service: TripoSplat image -> 3D Gaussian splat PLY, as an authenticated async network service.

Pattern follows the samcloud image-service model (a per-seat authenticated async job service).
every route needs a samcloud bearer (verified per call), jobs are async with an idempotency key,
inputs are fetched with the *caller's* bearer, outputs are uploaded under the service identity.
"""
import hashlib, json, logging, os, queue, signal, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import plane, worker

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

        def do_GET(self):
            who, _ = self._auth()
            if not who: return
            p = self.path.split("?")[0].rstrip("/")
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
