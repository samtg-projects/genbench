"""Task 1383: balanced thinning at a fixed N. Voxelise the stage (cell C), give each occupied cell a quota proportional to
(its summed importance)^ALPHA (ALPHA < 1 flattens the head's dominance), keep the top-imp splats per cell. Compare with plain importance.
Usage: thin3.py STAGE.ply OUT.png N [ALPHA ...]"""
import sys, numpy as np, cv2
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload, splat
ply, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3]); alphas = [float(a) for a in sys.argv[4:]] or [0.5]
sp = plyload.load(ply); s = sp["scale"]; imp = sp["opacity"] * (s[:, 0]*s[:, 1] + s[:, 1]*s[:, 2] + s[:, 0]*s[:, 2])
def balanced(alpha, C=0.04):
    key = np.floor(sp["pos"] / C).astype(np.int64); _, cell = np.unique(key, axis=0, return_inverse=True); cell = cell.ravel()
    tot = np.bincount(cell, imp); q = tot ** alpha; q = q / q.sum() * n
    order = np.lexsort((-imp, cell)); rank = np.empty(len(imp), int)
    starts = np.r_[0, np.cumsum(np.bincount(cell))[:-1]]; rank[order] = np.arange(len(imp)) - starts[cell[order]]
    keep = rank < np.maximum(1, np.round(q[cell])).astype(int)
    i = np.nonzero(keep)[0]
    if len(i) > n: i = i[np.argsort(-imp[i])[:n]]
    return i
V = [("importance only", np.argsort(-imp)[:n])] + [(f"balanced a={a}", balanced(a)) for a in alphas] + [("full", np.arange(len(imp)))]
o = sp["opacity"] > 0.5; P = sp["pos"][o]; t0, b0 = np.percentile(P[:, 1], 0.5), np.percentile(P[:, 1], 99.5)
leaf = np.median(P[(P[:, 1] > t0 + 0.7 * (b0 - t0)) & (np.abs(P[:, 2]) > 0.1)], 0)
cams = [((3.0, 0, 0), (0, 0, 0), 900), (tuple(leaf + [1.0, 0, 0]), tuple(leaf), 1400)]
rows = []
for name, i in V:
    t = {k: v[i] for k, v in sp.items()}; row = []
    for eye, tgt, f in cams:
        R, tt = splat.look_at(eye, tgt, up=(0, -1, 0)); img, _ = splat.render(t, R, tt, f, 380, 460, (0.03, 0.03, 0.035))
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1].copy()
        cv2.putText(img, f"{name} ({len(i)//1000}k)", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA); row.append(img)
    rows.append(np.vstack(row))
cv2.imwrite(out, np.hstack(rows))
