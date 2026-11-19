"""One rigid rotation for a whole set: stand REF's base->top-centre line upright about the shared base (0, 0.47, 0), apply it
to every PLY, then one uniform scale so REF reaches HEIGHT. Usage: setrot.py REF HEIGHT ply..."""
import sys, numpy as np
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload
ref, h, ps = sys.argv[1], float(sys.argv[2]), sys.argv[3:]; piv = np.array([0, 0.47, 0])
sp = plyload.load(ref); P, o = sp["pos"], sp["opacity"] > 0.5
top = np.percentile(P[o, 1], 0.5); Hh = 0.47 - top
b0 = np.median(P[o & (P[:, 1] > 0.47 - 0.05 * Hh)], 0); t0 = np.median(P[o & (P[:, 1] < top + 0.3 * Hh)], 0)
d = (t0 - b0) / np.linalg.norm(t0 - b0); tgt = np.array([0, -1.0, 0]); v = np.cross(d, tgt); s = np.linalg.norm(v); c = d @ tgt
K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); R = np.eye(3) + K + K @ K * ((1 - c) / s**2)
print("tilt", round(float(np.degrees(np.arccos(c))), 1))
def apply(sp, M):
    A = sp["axes"] * sp["scale"][:, :, None]; S = np.einsum("nki,nkj->nij", A, A); S = M @ S @ M.T
    w, V = np.linalg.eigh(S); sp["scale"] = np.sqrt(np.clip(w, 1e-14, None)); sp["axes"] = np.swapaxes(V, 1, 2)
sps = [plyload.load(p) for p in ps]
for x in sps: x["pos"] = (x["pos"] - piv) @ R.T + piv; apply(x, R)
r = sps[ps.index(ref)] if ref in ps else None
rr = r if r is not None else sp
o = rr["opacity"] > 0.5; g = h / (0.47 - np.percentile(rr["pos"][o, 1], 0.5))
for p, x in zip(ps, sps): x["pos"] = piv + (x["pos"] - piv) * g; x["scale"] *= g; plyload.save(p, x)
print("scale", round(float(g), 3))
