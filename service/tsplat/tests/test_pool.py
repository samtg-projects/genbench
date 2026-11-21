"""Registry pool worker against a fake registry: claim -> presigned input -> splat -> presigned PUT -> complete / fail."""
import hashlib, json, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tsplat_service import pool, registry, worker

IMG = b"\x89PNG fake image bytes"
SEEN = {"calls": [], "put": None, "complete": None, "fail": None}
CLAIMS = []                                                     # what successive claims return


class FakeRegistry(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _j(self, obj):
        b = json.dumps(obj).encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):                                           # presigned input URL: no bearer expected
        SEEN["calls"].append(("GET", self.path, self.headers.get("Authorization")))
        if "/running?" in self.path:
            return self._j({"items": [{"id": "T7", "preset": "image-to-splat", "worker": "tsplat-obelisk:111"}]})
        self.send_response(200); self.send_header("Content-Length", str(len(IMG))); self.end_headers(); self.wfile.write(IMG)

    def do_PUT(self):
        SEEN["put"] = (self.path, self.headers.get("Authorization"), self.rfile.read(int(self.headers["Content-Length"])))
        self._j({})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); body = json.loads(self.rfile.read(n) or b"{}")
        SEEN["calls"].append(("POST", self.path, self.headers.get("Authorization")))
        if self.path.endswith("/upload"): return self._j({"storage_key": "stg/outputs/T1/splat.ply", "url": f"{BASE}/presigned-put/splat.ply"})
        if self.path.endswith("/complete"): SEEN["complete"] = body; return self._j({"ok": True})
        if self.path.endswith("/fail"): SEEN["fail"] = body; return self._j({"ok": True})
        if self.path.endswith("/requeue"): return self._j({"status": "queued"})
        self._j({"job": CLAIMS.pop(0) if CLAIMS else None})


srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeRegistry); threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_port}"


class G:
    def save_ply(self, p): Path(p).write_bytes(b"ply bytes")


class FakeWarm:
    def __init__(self, warm=False):
        self.gpu = threading.Lock(); self.pipe = object() if warm else None; self.ensured = 0; self.last_used = 0; self.srcs = []
    def ensure(self):
        assert self.gpu.locked(); self.ensured += 1; self.pipe = object()
    def splat(self, src, matte, n, work, timings):
        assert self.gpu.locked() and Path(src).read_bytes() == IMG and matte in ("opaque", "auto")
        self.srcs.append(Path(src).name); timings["splat_s"] = 1.0
        return G(), None, matte


@pytest.fixture
def p(tmp_path, monkeypatch):
    (tmp_path / "tok").write_text("pooltoken\n")
    monkeypatch.setattr(registry, "measure", lambda ply: {"frame": "ply", "up": [0.0, -1.0, 0.0], "view": [-1.0, 0.0, 0.0], "center": [0, 0, 0], "height": 1.0})
    cfg = {"state_dir": str(tmp_path), "registry_pool": {"url": BASE, "pool": "tsplat-obelisk", "token_file": str(tmp_path / "tok")}}
    for k in ("put", "complete", "fail"): SEEN[k] = None
    SEEN["calls"].clear(); CLAIMS.clear()
    return pool.Pool(cfg, FakeWarm())


def job(sha=None, matte="opaque", tid="T1"):
    return {"id": tid, "params": {"matte": matte}, "input_assets": [{"asset": {"id": "A1"}, "files": [
        {"role": "source", "mime": "image/png", "url": f"{BASE}/presigned-get/in.png", "sha256": sha or hashlib.sha256(IMG).hexdigest()}]}]}


def run_locked(p, j):
    with p.warm.gpu: p.run_job(j)


def test_job_completes_with_ply_and_frame(p):
    run_locked(p, job())
    get = [c for c in SEEN["calls"] if c[0] == "GET"][-1]
    assert get[2] is None                                            # presigned input read without our bearer
    assert SEEN["put"][2] == b"ply bytes" and SEEN["put"][1] is None
    out = SEEN["complete"]["outputs"][0]
    assert out["storage_key"] == "stg/outputs/T1/splat.ply" and out["sha256"] == hashlib.sha256(b"ply bytes").hexdigest()
    assert {"up", "center"} <= set(out["meta"]["splatFrame"]) and out["meta"]["matte_used"] == "opaque"
    posts = [c for c in SEEN["calls"] if c[0] == "POST"]
    assert all(c[2] == "Bearer pooltoken" for c in posts)            # pool calls carry the pool bearer
    assert SEEN["fail"] is None


def test_bad_input_hash_is_reported_as_fail(p):
    run_locked(p, job(sha="0" * 64))
    assert SEEN["complete"] is None and "sha256" in SEEN["fail"]["error"]


def test_bad_matte_param_fails_cleanly(p):
    run_locked(p, job(matte="magic"))
    assert SEEN["complete"] is None and "matte" in SEEN["fail"]["error"]


def test_pool_stays_off_without_its_token(tmp_path):
    cfg = {"state_dir": str(tmp_path), "registry_pool": {"url": BASE, "pool": "x", "token_file": str(tmp_path / "none")}}
    assert pool.start(cfg) is None


def posts(p): return [c[1].rsplit("/", 1)[-1].split("?")[0] for c in SEEN["calls"] if c[0] == "POST"]


def test_cold_worker_hands_the_job_back_while_it_waits_for_the_gpu(p):
    CLAIMS.extend([job(tid="T1"), job(tid="T1")])                 # probe, then the real claim after the lease
    assert p.step() is True
    assert posts(p)[:3] == ["claim", "requeue", "claim"]           # never holds a claim across ensure()
    assert p.warm.ensured == 1 and SEEN["complete"] and p.warm.srcs == ["input.png"]


def test_warm_free_worker_runs_straight_away(p):
    p.warm.pipe = object(); CLAIMS.append(job(tid="T2"))
    assert p.step() is True
    assert "requeue" not in posts(p) and p.warm.ensured == 0 and SEEN["complete"]


def test_warm_but_busy_gpu_also_hands_back(p):
    p.warm.pipe = object(); CLAIMS.extend([job(tid="T3")])          # gone by the time we reclaim
    p.warm.gpu.acquire()
    t = threading.Timer(0.2, p.warm.gpu.release); t.start()
    assert p.step() is False
    assert posts(p) == ["claim", "requeue", "claim"] and SEEN["complete"] is None


def test_shutdown_requeues_the_job_in_flight(p, monkeypatch):
    monkeypatch.setattr(pool, "POOL", p); p.current = "T9"
    pool.requeue_on_exit()
    assert ("POST", "/api/pools/tsplat-obelisk/jobs/T9/requeue", "Bearer pooltoken") in SEEN["calls"]


def test_startup_requeues_what_a_dead_run_left_running(p):
    assert p.recover() == ["T7"]
    assert ("GET", "/api/pools/tsplat-obelisk/running?host=tsplat-obelisk", "Bearer pooltoken") in SEEN["calls"]
    assert posts(p) == ["requeue"]
    assert p.worker_name.startswith("tsplat-obelisk:")                # claims are tagged host:pid


def test_idle_release_rechecks_after_waiting_for_the_gpu_lock(tmp_path, monkeypatch):
    """22 Nov: the idle check passed while a pool run held warm.gpu, then released the moment the run ended."""
    import queue as qmod
    released = []
    w = worker.Warm({"triposplat_repo": str(tmp_path)}, None)
    w.lease = "L"; w.last_used = 0                                    # stale before the run
    monkeypatch.setattr(w, "release", lambda: released.append(1))
    class Jobs:
        q = qmod.Queue()
    monkeypatch.setattr(worker, "Warm", lambda cfg, me: w)
    w.gpu.acquire()                                                   # the pool's run is in progress
    t = threading.Thread(target=worker.run, args=({"plane_url": "x", "idle_release_s": 0.1, "state_dir": str(tmp_path)}, Jobs, None), daemon=True)
    t.start(); import time; time.sleep(0.3)
    w.last_used = time.time() + 60                                     # the run finishes and stamps last_used
    w.gpu.release(); time.sleep(0.3)
    assert released == []
