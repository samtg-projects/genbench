"""Task 1384, iris: put each stage's disc in one frame. ICP can't register a flat ring whose hole changes size, so each
stage is normalised by its own disc: centre to the shared point, its plane's normal (opacity-weighted PCA) turned onto +x
(face-on to the registry view -1,0,0) by the minimal rotation, and its rim (from the 90th-percentile in-plane radius of splats on the disc) to RADIUS.
    iris_norm.py RADIUS ply...   (in place)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload
rad, ps = float(sys.argv[1]), sys.argv[2:]; ctr_out = np.array([0, 0.47 - rad, 0])
def apply(sp, M):
    A = sp["axes"] * sp["scale"][:, :, None]; S = np.einsum("nki,nkj->nij", A, A); S = M @ S @ M.T
    w, V = np.linalg.eigh(S); sp["scale"] = np.sqrt(np.clip(w, 1e-14, None)); sp["axes"] = np.swapaxes(V, 1, 2)
for p in ps:
    sp = plyload.load(p); o = sp["opacity"] > 0.3; P = sp["pos"][o]; w = sp["opacity"][o]
    c = np.median(P, 0); X = P - c; C = (X * w[:, None]).T @ X / w.sum(); ev, V = np.linalg.eigh(C); n = V[:, 0]
    if n[0] < 0: n = -n
    tgt = np.array([1.0, 0, 0]); v = np.cross(n, tgt); s = np.linalg.norm(v); cth = n @ tgt
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); R = np.eye(3) + K + (K @ K) * ((1 - cth) / max(s * s, 1e-12)) if s > 1e-9 else np.eye(3)
    Y = X @ R.T; near = np.abs(Y[:, 0]) < 3 * np.percentile(np.abs(Y[:, 0]), 50)    # on the disc, not floaters
    r = np.percentile(np.hypot(Y[near, 1], Y[near, 2]), 90) / 0.95; g = rad / r      # 90th pct of a disc is 0.95 R
    sp["pos"] = ctr_out + ((sp["pos"] - c) @ R.T) * g; apply(sp, R); sp["scale"] *= g; plyload.save(p, sp)
    print(os.path.basename(p), "tilt", round(float(np.degrees(np.arccos(np.clip(cth, -1, 1)))), 1), "rim", round(float(r), 3), "scale", round(float(g), 3))
