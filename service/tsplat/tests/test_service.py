"""HTTP, auth, job and fallback tests with a fake plane and a fake TripoSplat pipeline (no torch needed)."""
import json, sys, threading, time, types, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tsplat_service import server, worker, plane

REAL_MEASURE = worker.registry.measure
REAL_ENSURE = worker.Warm.ensure              # the svc fixture stubs it; the queued-lease test needs the real one

USERS = {"Bearer good": {"valid": True, "user_id": 7, "username": "alice", "groups": [{"slug": "work"}]},
         "Bearer other": {"valid": True, "user_id": 8, "username": "bob", "groups": ["work"]},
         "Bearer outsider": {"valid": True, "user_id": 9, "username": "eve", "groups": ["guests"]},
         "Bearer svc": {"valid": True, "user_id": 99, "username": "service-tsplat", "groups": ["services"]}}
SEEN = {"fetch_bearers": [], "uploads": [], "comments": [], "leases": [], "links": {}, "reg": []}
READABLE = {"Bearer good": {7001, 4242}, "Bearer other": {7001, 7}, "Bearer svc": {7001, 7}}


class FakePlane(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _j(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        a = self.headers.get("Authorization")
        if self.path == "/api/v1/auth/verify":
            return self._j(200, USERS[a]) if a in USERS else self._j(401, {"valid": False})
        if self.path.startswith("/api/v1/files/") and self.path.endswith("/raw"):
            SEEN["fetch_bearers"].append(a)
            if a == "Bearer other": return self._j(403, {"detail": "no access"})
            from PIL import Image; import io
            buf = io.BytesIO(); Image.new("RGB", (64, 64), (200, 10, 10)).save(buf, "PNG")
            b = buf.getvalue(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if self.path.startswith("/api/transforms/"):
            SEEN["reg"].append(("GET", self.path, a))
            return self._j(200, {"/t1": {"id": "t1", "preset": "ply-to-dgs", "status": "completed", "next": "t2", "outputs": ["d1"]},
                                 "/t2": {"id": "t2", "preset": "dgs-to-bundle", "status": "completed", "next": "t3", "outputs": ["b1"]},
                                 "/t3": {"id": "t3", "preset": "splat-thumb", "status": "completed", "next": None, "outputs": ["img9"]}}
                           [self.path[self.path.rindex("/"):]])                     # live chain has an auto splat-thumb after the bundle
        if self.path == "/api/assets/b1":
            return self._j(200, {"id": "b1", "meta": {"splatFrame": {"up": [0, -1, 0], "view": [0, 0, 1], "height": 0.8}}})
        if "/wait" in self.path: return self._j(200, {"lease_id": "L1", "status": "active"})
        if self.path.startswith("/api/v1/tasks/"):
            tid = int(self.path.rsplit("/", 1)[1])
            return self._j(200, {"id": tid}) if tid in READABLE.get(a, set()) else self._j(404, {})
        if self.path.startswith("/api/v1/files/"):
            fid = int(self.path.rsplit("/", 1)[1])
            return self._j(200, {"id": fid, "links": SEEN["links"].get(fid, [])})
        self._j(404, {})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n)
        if self.path in ("/api/files", "/api/assets", "/api/transforms"):
            b = json.loads(body); SEEN["reg"].append(("POST", self.path, b, self.headers.get("Authorization")))
            return self._j(201, {"/api/files": {"file": {"id": "f1"}}, "/api/assets": {"id": "a1"}, "/api/transforms": {"id": "t1"}}[self.path])
        if self.path == "/api/v1/files":
            SEEN["uploads"].append(self.headers.get("Authorization")); return self._j(200, {"id": 1000 + len(SEEN["uploads"])})
        if self.path.endswith("/leases"):
            SEEN["leases"].append(json.loads(body)); return self._j(200, {"lease_id": "L1", "status": "queued", "queue_position": 1})
        if self.path.endswith("/renew"): return self._j(200, {"status": "active"})
        if self.path.startswith("/api/v1/files/") and self.path.endswith("/links"):
            fid = int(self.path.split("/")[4]); b = json.loads(body); lid = 5000 + sum(map(len, SEEN["links"].values()))
            SEEN["links"].setdefault(fid, []).append({"id": lid, "target_type": b["target_type"], "target_id": b["target_id"]})
            return self._j(200, {"status": "linked", "link_id": lid})
        if self.path.endswith("/comments"):
            SEEN["comments"].append((self.path, json.loads(body))); return self._j(200, {"id": 1})
        self._j(404, {})

    def do_PUT(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0)); SEEN["reg"].append(("PUT", self.path)); self._j(200, {})

    def do_PATCH(self):
        b = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0))); SEEN["reg"].append(("PATCH", self.path, b)); self._j(200, {})

    def do_DELETE(self): self._j(200, {})


class FakeGauss:
    def save_ply(self, p): Path(p).write_bytes(b"ply\n")


class FakePrepared:
    def save(self, p): Path(p).write_bytes(b"RIFF")


class FakePipe:
    calls = []

    def run(self, path, num_gaussians, show_progress):
        from PIL import Image
        im = Image.open(path); FakePipe.calls.append((Path(path).name, im.mode))
        if im.mode != "RGBA": raise ValueError("zero-size array to reduction operation minimum which has no identity")
        return FakeGauss(), FakePrepared()


@pytest.fixture(scope="module")
def svc(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("svc")
    fp = ThreadingHTTPServer(("127.0.0.1", 0), FakePlane); threading.Thread(target=fp.serve_forever, daemon=True).start()
    api = f"http://127.0.0.1:{fp.server_port}/api/v1"
    (tmp / "tok").write_text("Authorization: Bearer svc\n")
    cfg = {"plane_url": api, "state_dir": str(tmp / "state"), "port": 0, "allowed_groups": ["work", "services"],
           "principal": {"token_file": str(tmp / "tok"), "expected_username": "service-tsplat", "expected_user_id": 99},
           "resource_id": "gpu-metal", "memory_mb": 16384, "idle_release_s": 1, "renewal_interval": 30,
           "file_group": "tsplat-service-sink", "triposplat_repo": str(tmp),
           "publish_enabled": True, "registry_url": api.rsplit("/api/v1", 1)[0], "registry_group": "tsplat-drafts", "registry_poll_s": 0.05}
    (tmp / "state").mkdir()
    me = plane.Principal(cfg); me.check()
    worker.Warm.ensure = lambda self: self.pipe or (setattr(self, "lease", self.me.lease_acquire()), setattr(self, "pipe", FakePipe()), self.pipe)[2]
    def stub(name):
        def f(ply, work):
            (work / name).write_bytes(b"x"); return work / name
        return f
    worker.render.beauty, worker.render.sheet = stub("b.png"), stub("s.jpg")
    worker.registry.measure = lambda ply: {"frame": "ply", "up": [0.0, -1.0, 0.0], "view": [-1.0, 0.0, 0.0], "center": [0, 0, 0], "height": 1.0}
    jobs = server.Jobs(tmp / "state")
    threading.Thread(target=worker.run, args=(cfg, jobs, me), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.make_handler(cfg, jobs, plane.Auth(cfg), me))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_port}"


def call(base, path, bearer=None, body=None, idem=None):
    h = {"Content-Type": "application/json"}
    if bearer: h["Authorization"] = bearer
    if idem: h["Idempotency-Key"] = idem
    r = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=h,
                               method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(r, timeout=10) as resp: return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read())


def test_health_requires_bearer(svc):
    assert call(svc, "/health")[0] == 401
    assert call(svc, "/health", "Bearer nope")[0] == 401
    assert call(svc, "/health", "Bearer outsider")[0] == 403
    st, h = call(svc, "/health", "Bearer good"); assert st == 200 and h["service"] == "tsplat-service"


RT = {"kind": "task", "id": 7001}


def test_validation(svc):
    assert call(svc, "/v1/splat", "Bearer good", {"file_id": "x", "reply_to": RT})[0] == 400
    assert call(svc, "/v1/splat", "Bearer good", {"file_id": 1, "matte": "magic", "reply_to": RT})[0] == 400
    assert call(svc, "/v1/splat", "Bearer good", {"file_id": 1, "num_gaussians": 10, "reply_to": RT})[0] == 400
    assert call(svc, "/v1/splat", "Bearer good", {"file_id": 1, "publish": {"group_id": "x"}, "reply_to": RT})[0] == 400
    st, e = call(svc, "/v1/splat", "Bearer good", {"file_id": 1}); assert st == 400 and "reply_to" in e["error"]


def test_reply_to_checked_at_submit(svc):
    n = len(SEEN["fetch_bearers"])
    assert call(svc, "/v1/splat", "Bearer good", {"file_id": 1, "reply_to": {"kind": "task", "id": 7}})[0] == 403    # caller can't read
    st, e = call(svc, "/v1/splat", "Bearer good", {"file_id": 1, "reply_to": {"kind": "task", "id": 4242}})           # service can't read
    assert st == 403 and "service" in e["error"]
    assert len(SEEN["fetch_bearers"]) == n                                                                         # no work started


def test_job_end_to_end_with_fallback_and_caller_fetch(svc):
    st, j = call(svc, "/v1/splat", "Bearer good", {"file_id": 3363, "reply_to": {"kind": "task", "id": 7001}}, idem="k1")
    assert st == 202 and j["state"] == "queued"
    st2, j2 = call(svc, "/v1/splat", "Bearer good", {"file_id": 3363, "reply_to": {"kind": "task", "id": 7001}}, idem="k1")
    assert st2 == 200 and j2["id"] == j["id"]                                  # idempotent
    st, done = call(svc, f"/v1/jobs/{j['id']}/wait?timeout_s=10", "Bearer good")
    assert done["state"] == "done", done
    assert done["result"]["matte_used"].startswith("auto→opaque")              # empty-matte fallback
    assert [c[1] for c in FakePipe.calls[-2:]] == ["RGB", "RGBA"]
    assert "Bearer good" in SEEN["fetch_bearers"] and "Bearer svc" not in SEEN["fetch_bearers"]  # caller's bearer, not ours
    assert set(SEEN["uploads"]) == {"Bearer svc"}
    assert SEEN["leases"][0]["memory_mb"] == 16384
    assert {"lease_wait_s", "load_s", "splat_s"} <= set(done["timings"])
    assert SEEN["comments"] and SEEN["comments"][-1][0] == "/api/v1/tasks/7001/comments"
    links = done["result"]["links"]
    assert set(links) == {"ply_file_id", "prepared_file_id", "beauty_file_id", "sheet_file_id"}
    for k, lid in links.items():                                                # every output linked to reply_to
        assert {"id": lid, "target_type": "task", "target_id": "7001"} in SEEN["links"][done["result"][k]]


def test_other_user_cannot_see_job_and_unreadable_input_fails(svc):
    st, j = call(svc, "/v1/splat", "Bearer good", {"file_id": 5, "reply_to": RT}, idem="k2")
    assert call(svc, f"/v1/jobs/{j['id']}", "Bearer other")[0] == 404
    st, j = call(svc, "/v1/splat", "Bearer other", {"file_id": 6, "reply_to": RT}, idem="k3")
    st, done = call(svc, f"/v1/jobs/{j['id']}/wait?timeout_s=10", "Bearer other")
    assert done["state"] == "failed" and "403" in done["error"]
    st, again = call(svc, "/v1/splat", "Bearer other", {"file_id": 6, "reply_to": RT}, idem="k3")   # failed key starts a new job
    assert st == 202 and again["id"] != j["id"]


def test_idle_release(svc):
    time.sleep(2.5)
    assert worker.STATE["loaded"] is False or worker.STATE["lease"] is None


def test_release_on_exit_gives_lease_back(svc):
    class Me:
        released = []
        def lease_release(self, lid): Me.released.append(lid)
    w = worker.Warm({}, Me()); w.lease = "L9"; worker.WARM = w
    worker.release_on_exit()
    assert Me.released == ["L9"] and w.lease is None
    worker.release_on_exit()                                   # idempotent: nothing held, nothing sent
    assert Me.released == ["L9"]


def test_queued_lease_is_known_before_grant(svc, tmp_path):
    """SIGTERM while queued: the lease id is already on Warm, so release_on_exit withdraws it."""
    seen = {}
    class Me:
        def lease_acquire(self, on_id=None):
            on_id("Lq"); seen["during_wait"] = w.lease; raise SystemExit("terminated while queued")
        released = []
        def lease_release(self, lid): Me.released.append(lid)
    w = worker.Warm({"triposplat_repo": str(tmp_path)}, Me()); worker.WARM = w
    with pytest.raises(SystemExit):
        REAL_ENSURE(w)
    assert seen["during_wait"] == "Lq"
    worker.release_on_exit()
    assert Me.released == ["Lq"]


def test_publish_lands_in_drafts_and_fixes_view(svc):
    st, j = call(svc, "/v1/splat", "Bearer good", {"file_id": 7002, "reply_to": RT, "publish": {"name": "SCOOT"}}, idem="pub1")
    assert st == 202
    call(svc, f"/v1/jobs/{j['id']}/wait?timeout_s=10", "Bearer good")
    for _ in range(100):
        r = call(svc, f"/v1/jobs/{j['id']}", "Bearer good")[1]["result"]["registry"]
        if r["state"] != "converting": break
        time.sleep(0.05)
    assert r["state"] == "published" and r["bundle"] == "b1" and r["transforms"] == ["t1", "t2"], r
    posts = [e for e in SEEN["reg"] if e[0] == "POST"]
    assert posts[0][2]["group_id"] == "tsplat-drafts" and posts[1][2]["group_id"] == "tsplat-drafts"        # always the drafts group
    assert posts[1][2]["type"] == "splat-ply" and posts[1][2]["name"] == "SCOOT"
    assert {"up", "center"} <= set(posts[1][2]["meta"]["splatFrame"])                              # the registry's required pair
    assert posts[2][2] == {"preset": "ply-to-dgs", "inputs": ["a1"], "params": {"up": [0.0, -1.0, 0.0]}}
    assert {p[3] for p in posts} == {"Bearer svc"}                                                 # the service's bearer
    patch = [e for e in SEEN["reg"] if e[0] == "PATCH"][-1]
    assert patch[1] == "/api/assets/b1" and patch[2]["meta"]["splatFrame"] == {"up": [0.0, -1.0, 0.0], "view": [-1.0, 0.0, 0.0], "height": 0.8}
    assert any("bundle `b1`" in c[1]["body"] for c in SEEN["comments"])


def test_publish_failure_still_delivers_the_splat(svc):
    real = worker.registry.Registry.start
    def boom(self, ply, name): raise RuntimeError("registry POST /api/files: 403 no access")
    worker.registry.Registry.start = boom
    try:
        st, j = call(svc, "/v1/splat", "Bearer good", {"file_id": 3368, "reply_to": RT, "publish": {}}, idem="pubfail")
        st, done = call(svc, f"/v1/jobs/{j['id']}/wait?timeout_s=10", "Bearer good")
    finally:
        worker.registry.Registry.start = real
    assert done["state"] == "done", done
    assert done["result"]["registry"]["state"] == "failed" and "403" in done["result"]["registry"]["error"]
    assert set(done["result"]["links"]) == {"ply_file_id", "prepared_file_id", "beauty_file_id", "sheet_file_id"}
    assert "Registry publish failed" in SEEN["comments"][-1][1]["body"]                     # the caller hears about it


def test_measure_on_a_real_ply(tmp_path, monkeypatch):
    """measure() on a small binary PLY: median centre and the 2-98 % extent along up (y-down)."""
    import numpy as np
    from tsplat_service import registry as reg
    rng = np.random.default_rng(0); n = 1000
    pts = np.stack([rng.uniform(-1, 1, n), rng.uniform(0, 2, n), rng.uniform(-1, 1, n)], -1).astype("<f4")
    class TC:
        @staticmethod
        def _read_ply_float_columns(path, cols): return {k: pts[:, i] for i, k in enumerate(cols)}
    monkeypatch.setattr("tsplat_service.render._thumb", lambda: TC)
    f = REAL_MEASURE(tmp_path / "x.ply")
    assert f["up"] == [0.0, -1.0, 0.0] and f["view"] == [-1.0, 0.0, 0.0] and f["frame"] == "ply"
    assert abs(f["center"][1] - 1.0) < 0.1 and abs(f["height"] - 1.92) < 0.1
