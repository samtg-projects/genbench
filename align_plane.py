# Task 1361: align each stage's leaf plane to S01's, so a keyed dissolve holds from the side.
# Opacity-weighted PCA gives each stage's plane normal; the minimal rotation (about the stage centroid) takes it onto
# S01's normal (sign-matched), then the centroid moves onto S01's. Positions and rot_0..3 (wxyz) are rotated; SH 0 needs nothing.
#   align_plane.py <in_dir> <out_dir> S01.ply S02. py ...
#   TARGET=1,0,0 aligns every stage's normal to that axis instead (front-on to the TripoSplat input view along +x).
import sys, os, numpy as np
from pathlib import Path

def read(p):
    b = open(p, "rb").read(); h = b.index(b"end_header\n") + 11; head = b[:h].decode()
    n = int(head.split("element vertex ")[1].split("\n")[0])
    props = [l.split()[-1] for l in head.splitlines() if l.startswith("property float")]
    assert "format binary_little_endian" in head and len(props) == len(head.split("property ")) - 1, "all-float layout only"
    return head, np.frombuffer(b[h:], dtype=[(k, "<f4") for k in props], count=n).copy()

def plane(v):
    xyz = np.stack([v["x"], v["y"], v["z"]], -1).astype(np.float64)
    w = 1 / (1 + np.exp(-v["opacity"].astype(np.float64)))
    c = (xyz * w[:, None]).sum(0) / w.sum(); d = xyz - c
    cov = (d * w[:, None]).T @ d / w.sum(); ev, evec = np.linalg.eigh(cov)
    return c, evec[:, 0], ev                                     # smallest eigenvalue's vector = plane normal

def rot_between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b); v = np.cross(a, b); s = np.linalg.norm(v); c = a @ b
    if s < 1e-9: return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]) / s
    th = np.arctan2(s, c); return np.eye(3) + np.sin(th) * k + (1 - np.cos(th)) * k @ k

def mat2quat(R):                                                  # wxyz
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2; return np.array([s / 4, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s])
    i = np.argmax(np.diag(R)); j, k = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2; q = np.zeros(4)
    q[0] = (R[k, j] - R[j, k]) / s; q[1 + i] = s / 4; q[1 + j] = (R[j, i] + R[i, j]) / s; q[1 + k] = (R[k, i] + R[i, k]) / s
    return q

def qmul(a, b):                                                   # a * b, wxyz, b is (n,4)
    w1, x1, y1, z1 = a; w2, x2, y2, z2 = b.T
    return np.stack([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2], -1)

ind, outd = Path(sys.argv[1]), Path(sys.argv[2]); outd.mkdir(parents=True, exist_ok=True); names = sys.argv[3:]
_, ref = read(ind / names[0]); c0, n0, _ = plane(ref)
if os.environ.get("TARGET"): n0 = np.array([float(a) for a in os.environ["TARGET"].split(",")])
for nm in names:
    head, v = read(ind / nm); c, n, ev = plane(v)
    if n @ n0 < 0: n = -n
    R = rot_between(n, n0); ang = np.degrees(np.arccos(np.clip(n @ n0, -1, 1)))
    xyz = np.stack([v["x"], v["y"], v["z"]], -1).astype(np.float64)
    xyz = (xyz - c) @ R.T + c0
    v["x"], v["y"], v["z"] = xyz.T.astype(np.float32)
    q = np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], -1).astype(np.float64)
    q = qmul(mat2quat(R), q / np.linalg.norm(q, axis=1, keepdims=True))
    v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"] = q.T.astype(np.float32)
    open(outd / nm, "wb").write(head.encode() + v.tobytes())
    _, n2, _ = plane(v); n2 = n2 if n2 @ n0 >= 0 else -n2
    print(f"{nm}: tilt to target {ang:5.1f} deg -> {np.degrees(np.arccos(np.clip(n2 @ n0, -1, 1))):4.1f} deg after; centroid shift {np.linalg.norm(c - c0):.3f}; flatness {ev[0] / ev[1]:.3f}")
