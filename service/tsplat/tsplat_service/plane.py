"""samcloud plane calls: caller verification, the service's own identity, files, comments and leases."""
import json, logging, mimetypes, threading, time, urllib.error, urllib.request, uuid
from pathlib import Path

log = logging.getLogger("tsplat.plane")


def _req(url, bearer, method="GET", data=None, headers=None, timeout=60):
    h = {"Authorization": bearer}
    h.update(headers or {})
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.status, resp.read()


def _json(url, bearer, method="GET", obj=None, timeout=60):
    data = json.dumps(obj).encode() if obj is not None else None
    st, b = _req(url, bearer, method, data, {"Content-Type": "application/json"} if data else None, timeout)
    return st, (json.loads(b) if b else None)


class Auth:
    """Verify a caller's bearer with /auth/verify; cache positive answers briefly."""

    def __init__(self, cfg):
        self.api = cfg["plane_url"].rstrip("/"); self.cache = {}; self.lock = threading.Lock()

    def verify(self, bearer):
        if not bearer.startswith("Bearer ") or len(bearer) > 512: return None
        now = time.time()
        with self.lock:
            hit = self.cache.get(bearer)
            if hit and hit[0] > now: return hit[1]
        try:
            st, v = _json(f"{self.api}/auth/verify", bearer, timeout=15)
        except (urllib.error.URLError, ValueError):
            return None
        if st != 200 or not v or not v.get("valid") or not isinstance(v.get("user_id"), int) or not v.get("username"):
            return None
        who = {"username": v["username"], "user_id": v["user_id"], "groups": [g if isinstance(g, str) else g.get("slug", g.get("name"))
                                                                              for g in v.get("groups", [])]}
        with self.lock:
            self.cache[bearer] = (now + 60, who)
        return who


class Principal:
    """The service's own plane identity: holds the GPU lease, uploads outputs, posts reply_to comments."""

    def __init__(self, cfg):
        self.cfg = cfg; self.api = cfg["plane_url"].rstrip("/")
        p = cfg["principal"]
        self.token_file = Path(p["token_file"]).expanduser()
        self.username = p["expected_username"]

    def hdr(self):
        """The Authorization value; the token file holds a raw token or an `Authorization: Bearer …` header line."""
        t = self.token_file.read_text().strip()
        if t.lower().startswith("authorization:"):
            return t.split(":", 1)[1].strip()
        return t if t.startswith("Bearer ") else f"Bearer {t}"

    def check(self):
        p = self.cfg["principal"]
        st, v = _json(f"{self.api}/auth/verify", self.hdr(), timeout=15)
        if st != 200 or not v.get("valid") or v.get("username") != p["expected_username"] or \
                (p.get("expected_user_id") and v.get("user_id") != p["expected_user_id"]):
            raise SystemExit(f"principal mismatch: token is {v.get('username')!r}, expected {p['expected_username']!r}")
        log.info("principal ok: %s (user %s)", v["username"], v.get("user_id"))

    def upload(self, path: Path, group_scope=None):
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return upload_bytes(self.api, self.hdr(), path.name, path.read_bytes(), ctype, group_scope)

    def can_read(self, kind, oid):
        return caller_can_read(self.api, self.hdr(), kind, oid)

    def link(self, file_id, kind, oid):
        """Link an output to the reply_to object, then confirm the link on the file; returns the link id."""
        st, v = _json(f"{self.api}/files/{file_id}/links", self.hdr(), "POST", {"target_type": kind, "target_id": str(oid)})
        lid = v.get("link_id")
        _, f = _json(f"{self.api}/files/{file_id}", self.hdr())
        if not any(l.get("id") == lid and l.get("target_type") == kind and str(l.get("target_id")) == str(oid)
                   for l in f.get("links", [])):
            raise RuntimeError(f"link of file {file_id} to {kind} {oid} not confirmed")
        return lid

    def comment(self, kind, oid, body):
        plural = {"task": "tasks", "ticket": "tickets"}[kind]
        return _json(f"{self.api}/{plural}/{oid}/comments", self.hdr(), "POST", {"body": body})

    # GPU lease on the configured resource, held while the model is loaded.
    def lease_acquire(self, on_id=None):
        """Request the lease and block until granted; on_id(lid) runs as soon as the id exists, queued or not."""
        c = self.cfg
        body = {"memory_mb": c["memory_mb"], "ttl_seconds": c.get("ttl_seconds", 120), "wait": True,
                "max_total_s": c.get("max_total_s", 21600)}
        if c.get("service_id"): body["service_id"] = c["service_id"]
        unwrap = lambda v: v.get("lease", v) if isinstance(v, dict) else v
        st, lease = _json(f"{self.api}/resources/{c['resource_id']}/leases", self.hdr(), "POST", body)
        lease = unwrap(lease); lid = lease.get("lease_id") or lease["id"]   # the plane answers lease_id
        if on_id: on_id(lid)
        while lease.get("status") == "queued":
            try:
                _, lease = _json(f"{self.api}/leases/{lid}/wait?timeout_s=30", self.hdr(), timeout=45); lease = unwrap(lease)
            except urllib.error.URLError:
                time.sleep(5)
        if lease.get("status") != "active":
            raise RuntimeError(f"lease not granted: {lease.get('status')}")
        return lid

    def lease_renew(self, lid):
        st, v = _json(f"{self.api}/leases/{lid}/renew", self.hdr(), "POST", {"ttl_seconds": self.cfg.get("ttl_seconds", 120)})
        return v

    def lease_release(self, lid):
        try:
            _req(f"{self.api}/leases/{lid}", self.hdr(), "DELETE")
        except urllib.error.HTTPError as e:
            log.warning("lease release %s: %s", lid, e.code)


def caller_can_read(api, caller_bearer, kind, oid):
    """The service only comments where the caller could; this stops reply_to being used to post anywhere."""
    plural = {"task": "tasks", "ticket": "tickets"}[kind]
    try:
        st, _ = _req(f"{api.rstrip('/')}/{plural}/{oid}", caller_bearer, timeout=30)
        return st == 200
    except urllib.error.HTTPError:
        return False


def fetch_as_caller(api, caller_bearer, file_id, dest: Path):
    """Fetch an input with the caller's own bearer, so the service never reads what the caller cannot."""
    st, b = _req(f"{api.rstrip('/')}/files/{file_id}/raw", caller_bearer, timeout=120)
    dest.write_bytes(b)
    return dest


def upload_bytes(api, bearer, name, data, ctype, group_scope=None):
    """POST /files as whoever `bearer` is; returns the new file id."""
    boundary = uuid.uuid4().hex
    name = "".join(ch for ch in name if ch.isalnum() or ch in "._-")[:80] or "upload"
    parts = [f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
             f"Content-Type: {ctype}\r\n\r\n".encode(), data, b"\r\n"]
    if group_scope:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"group_scope\"\r\n\r\n{group_scope}\r\n".encode())
    parts.append(f"--{boundary}--\r\n".encode())
    st, b = _req(f"{api.rstrip('/')}/files", bearer, "POST", b"".join(parts),
                 {"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=300)
    return json.loads(b)["id"]


def raw_as_caller(api, caller_bearer, file_id):
    """Read a file with the caller's bearer (the test page's result viewer); returns (bytes, content type)."""
    r = urllib.request.Request(f"{api.rstrip('/')}/files/{int(file_id)}/raw", headers={"Authorization": caller_bearer})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return resp.read(), resp.headers.get("Content-Type", "application/octet-stream")
