"""Task 1383: where does the patchiness come from? One stage at full count vs thinned (N list), from front/side/back and a head close-up.
Thinning = the publish recipe as described: 2/3 of N by importance (opacity x projected area ~ s1*s2+s2*s3+s1*s3), 1/3 sampled by opacity.
Usage: diag.py STAGE.ply OUT.png N1 N2 ..."""
import sys, os, numpy as np, cv2
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload, splat
ply, out, Ns = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
sp = plyload.load(ply); rng = np.random.default_rng(0)
def thin(sp, n):
    if n >= len(sp["opacity"]): return sp
    s = sp["scale"]; imp = sp["opacity"] * (s[:, 0]*s[:, 1] + s[:, 1]*s[:, 2] + s[:, 0]*s[:, 2])
    a = np.argsort(-imp)[: 2 * n // 3]; rest = np.setdiff1d(np.arange(len(imp)), a)
    w = sp["opacity"][rest]; b = rng.choice(rest, n - len(a), replace=False, p=w / w.sum())
    i = np.concatenate([a, b]); return {k: v[i] for k, v in sp.items()}
o = sp["opacity"] > 0.5; P = sp["pos"][o]; top = np.percentile(P[:, 1], 0.5); bot = np.percentile(P[:, 1], 99.5)
head = np.median(P[P[:, 1] < top + 0.3 * (bot - top)], 0)
V = [("front", (3.0, 0, 0), (0, 0, 0), 900), ("side", (0, 0, -3.0), (0, 0, 0), 900), ("back", (-3.0, 0, 0), (0, 0, 0), 900),
     ("head close-up", tuple(head + np.array([1.2, 0, 0])), tuple(head), 1500)]
W, H = 420, 520; rows = []
for n in [len(sp["opacity"])] + Ns:
    t = thin(sp, n); row = []
    for name, eye, tgt, f in V:
        R, tt = splat.look_at(eye, tgt, up=(0, -1, 0))
        img, _ = splat.render(t, R, tt, f, W, H, (0.03, 0.03, 0.035))
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1].copy()
        cv2.putText(img, f"{n//1000}k  {name}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1, cv2.LINE_AA)
        row.append(img)
    rows.append(np.hstack(row))
cv2.imwrite(out, np.vstack(rows))
