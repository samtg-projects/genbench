"""Ending stages: scale each about the base so its mound's base width (x, the front view's horizontal, 10-90 pct of the
lowest 12% band) matches the first stage's, re-centre that band on x=z=0, then one factor so the first reaches HEIGHT.
Usage: mound.py HEIGHT ply..."""
import sys, numpy as np
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload
h, ps = float(sys.argv[1]), sys.argv[2:]; piv = np.array([0, 0.47, 0])
def band(sp):
    P, o = sp["pos"], sp["opacity"] > 0.5; top = np.percentile(P[o, 1], 0.5); m = o & (P[:, 1] > 0.47 - 0.12 * (0.47 - top))
    w = np.percentile(P[m, 2], 90) - np.percentile(P[m, 2], 10); return w, np.median(P[m, 0]), np.median(P[m, 2]), top
sps = [plyload.load(p) for p in ps]; w0 = band(sps[0])[0]
for sp in sps:
    w, cx, cz, _ = band(sp); sp["pos"] -= [cx, 0, cz]; g = w0 / w; sp["pos"] = piv + (sp["pos"] - piv) * g; sp["scale"] *= g; print("w", round(w, 3), "g", round(g, 3))
G = h / (0.47 - band(sps[0])[3])
for p, sp in zip(ps, sps):
    sp["pos"] = piv + (sp["pos"] - piv) * G; sp["scale"] *= G; plyload.save(p, sp)
print("G", round(G, 3))
