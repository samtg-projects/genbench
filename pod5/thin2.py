"""Task 1383 step 2: thinning options vs the full count, front + head close-up + leaf close-up.
imp = opacity x projected area; 'region' multiplies imp by HEADW for splats in the top HEADF of the stage's height."""
import sys, numpy as np, cv2
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload, splat
ply, out = sys.argv[1], sys.argv[2]
sp = plyload.load(ply); rng = np.random.default_rng(0); s = sp["scale"]; y = sp["pos"][:, 1]
area = s[:, 0]*s[:, 1] + s[:, 1]*s[:, 2] + s[:, 0]*s[:, 2]; imp = sp["opacity"] * area
o = sp["opacity"] > 0.5; t0, b0 = np.percentile(y[o], 0.5), np.percentile(y[o], 99.5)
def recipe(n):
    a = np.argsort(-imp)[: 2 * n // 3]; rest = np.setdiff1d(np.arange(len(imp)), a)
    w = sp["opacity"][rest]; return np.concatenate([a, rng.choice(rest, n - len(a), replace=False, p=w / w.sum())])
def byimp(n, headf=None, headw=1.0):
    v = imp.copy()
    if headf: v = v * np.where(y < t0 + headf * (b0 - t0), headw, 1.0)
    return np.argsort(-v)[:n]
V = [("30k current recipe", recipe(30000)), ("30k importance", byimp(30000)), ("30k importance, head x4", byimp(30000, 0.4, 4.0)),
     ("60k importance", byimp(60000)), ("60k importance, head x4", byimp(60000, 0.4, 4.0)), ("full 262k", np.arange(len(imp)))]
P = sp["pos"][o]; head = np.median(P[P[:, 1] < t0 + 0.3 * (b0 - t0)], 0)
leaf = np.median(P[(P[:, 1] > t0 + 0.7 * (b0 - t0)) & (np.abs(P[:, 2]) > 0.1)], 0)
cams = [((3.0, 0, 0), (0, 0, 0), 900), (tuple(head + [1.2, 0, 0]), tuple(head), 1500), (tuple(leaf + [1.0, 0, 0]), tuple(leaf), 1500)]
rows = []
for name, i in V:
    t = {k: v[i] for k, v in sp.items()}; row = []
    for eye, tgt, f in cams:
        R, tt = splat.look_at(eye, tgt, up=(0, -1, 0)); img, _ = splat.render(t, R, tt, f, 360, 440, (0.03, 0.03, 0.035))
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1].copy()
        cv2.putText(img, name, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA); row.append(img)
    rows.append(np.hstack(row))
cv2.imwrite(out, np.hstack([np.vstack(rows[:3]), np.vstack(rows[3:])]))
