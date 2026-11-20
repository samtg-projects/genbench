"""Register each stage onto a reference stage by trimmed ICP (rotation + uniform scale + translation; per iteration keep the
closest KEEP fraction of matches, so growth that the reference lacks is ignored). For anchor sets where TripoSplat re-centred and
re-scaled each stage by its own extent (a log or bark chip that should not move). Usage: register.py REF ply... (in place)"""
import sys, numpy as np, cv2
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload
import os
KEEP, IT, N = float(os.environ.get('KEEP', 0.7)), 40, 12000
LOWS, LOWT = float(os.environ.get('LOWS', 1.0)), float(os.environ.get('LOWT', 1.0))   # fraction of height (from the bottom) to match
ref, ps = sys.argv[1], sys.argv[2:]
rng = np.random.default_rng(0)
def sample(sp, frac=1.0):
    o = sp["opacity"] > 0.5; y = sp["pos"][:, 1]; b, t = np.percentile(y[o], 99.5), np.percentile(y[o], 0.5)
    i = np.nonzero(o & (y > b - frac * (b - t)))[0]; return sp["pos"][rng.choice(i, min(N, len(i)), replace=False)].astype(np.float32)
T = sample(plyload.load(ref), LOWT); idx = cv2.flann_Index(T, dict(algorithm=1, trees=4))
def umeyama(a, b):                     # b ~ s R a + t
    ma, mb = a.mean(0), b.mean(0); A, Bm = a - ma, b - mb
    U, S, Vt = np.linalg.svd(Bm.T @ A / len(a)); D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt; s = np.trace(np.diag(S) @ D) / (A ** 2).sum(1).mean(); return s, R, mb - s * R @ ma
STARTS = int(os.environ.get("STARTS", 1)); SMIN, SMAX = float(os.environ.get('SMIN', 0.7)), 1.4; MAXROT = float(os.environ.get('MAXROT', 180))
def rot_inits(n):
    if n == 1: return [np.eye(3)]
    g = np.random.default_rng(3); out = [np.eye(3)]
    while len(out) < n:
        q = g.normal(size=4); q /= np.linalg.norm(q); w, x, y, z = q
        out.append(np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)], [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)], [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]]))
    return out
for p in ps:
    sp = plyload.load(p); S0 = sample(sp, LOWS)
    # init: match the lower-band centre and the bottom, scale by the x-z spread of the lowest 30%
    def low(X): y = X[:, 1]; return X[y > np.percentile(y, 70)]
    best = None
    for R0 in rot_inits(STARTS):
        if STARTS == 1:
            s = np.sqrt(np.var(T[:, 2]) / np.var(S0[:, 2]))       # init: the log's length runs along z (the front view's horizontal)
            R = R0; t = np.array([np.median(T[:, 0]), T[:, 1].max(), np.median(T[:, 2])]) - s * np.array([np.median(S0[:, 0]), S0[:, 1].max(), np.median(S0[:, 2])])
        else:
            s = 1.0; R = R0; t = T.mean(0) - S0.mean(0) @ R.T
        for k in range(IT):
            X = (s * S0 @ R.T + t).astype(np.float32)
            nn, d = idx.knnSearch(X, 1, params={}); d = d[:, 0]
            keep = d <= np.quantile(d, KEEP)
            s, R, t = umeyama(S0[keep], T[nn[keep, 0]])
            if STARTS > 1 and not SMIN <= s <= SMAX:
                s = float(np.clip(s, SMIN, SMAX)); t = T[nn[keep, 0]].mean(0) - s * S0[keep].mean(0) @ R.T
        e = float(np.sqrt(np.quantile(d, KEEP)))
        if np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))) > MAXROT: continue
        if best is None or e < best[0]: best = (e, s, R, t)
    err, s, R, t = best
    sp["pos"] = s * sp["pos"] @ R.T + t
    A = sp["axes"] * (sp["scale"] * s)[:, :, None] @ R.T; S = np.einsum("nki,nkj->nij", A, A)
    w, V = np.linalg.eigh(S); sp["scale"] = np.sqrt(np.clip(w, 1e-14, None)); sp["axes"] = np.swapaxes(V, 1, 2)
    plyload.save(p, sp); print(p, "s", round(float(s), 3), "rot", round(float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))), 1), "t", np.round(t, 3), "trim-rms", round(err, 4))
