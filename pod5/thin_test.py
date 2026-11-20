"""Task 1383: 30k thinning variants on one stage, front + head close-up. Usage: thin_test.py STAGE.ply OUT.png N"""
import sys, numpy as np, cv2
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload, splat
ply, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
sp = plyload.load(ply); rng = np.random.default_rng(0); s = sp["scale"]
area = s[:, 0]*s[:, 1] + s[:, 1]*s[:, 2] + s[:, 0]*s[:, 2]; imp = sp["opacity"] * area
def take(i, boost=1.0):
    t = {k: v[i] for k, v in sp.items()}
    if boost != 1.0: t = dict(t); t["scale"] = t["scale"] * boost
    return t
a = np.argsort(-imp)[: 2 * n // 3]; rest = np.setdiff1d(np.arange(len(imp)), a)
w = sp["opacity"][rest]; b = rng.choice(rest, n - len(a), replace=False, p=w / w.sum())
top = np.argsort(-imp)[:n]
# coverage-preserving boost: scale up kept splats so their summed projected area matches the full set's (sqrt of the ratio)
k = float(np.sqrt(area[np.argsort(-imp)].sum() / area[top].sum()))
V = {"current recipe (2/3 imp + 1/3 opacity)": take(np.concatenate([a, b])),
     "importance only": take(top),
     f"importance only, scale x{k:.2f}": take(top, k),
     "full 262k": sp}
o = sp["opacity"] > 0.5; P = sp["pos"][o]; t0 = np.percentile(P[:, 1], 0.5); b0 = np.percentile(P[:, 1], 99.5)
head = np.median(P[P[:, 1] < t0 + 0.3 * (b0 - t0)], 0)
rows = []
for name, t in V.items():
    row = []
    for eye, tgt, f in (((3.0, 0, 0), (0, 0, 0), 900), (tuple(head + [1.2, 0, 0]), tuple(head), 1500)):
        R, tt = splat.look_at(eye, tgt, up=(0, -1, 0)); img, _ = splat.render(t, R, tt, f, 420, 520, (0.03, 0.03, 0.035))
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1].copy()
        cv2.putText(img, name, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA); row.append(img)
    rows.append(np.hstack(row))
cv2.imwrite(out, np.hstack([np.vstack(rows[:2]), np.vstack(rows[2:])]))
print("boost", round(k, 3))
