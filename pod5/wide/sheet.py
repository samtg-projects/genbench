"""Task 1384: a stage sheet with Trent's reference beside ours. One row per stage: Trent's frame, our klein still, and our
splat from the front and from 35 degrees, all splats from one fixed camera (so the anchor visibly holds).
    sheet.py OUT.jpg PLYDIR STILLDIR TRENT_PREFIX STAGES   e.g. sheet.py cham.jpg ply-cham pick-cham crops/cham C01,C02,...
Credit: built from Trent's concepts and references (doc 670). Renderer: claude-wafer's look-dev (hero/splat.py)."""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload, splat
out, plydir, stilldir, trent, stages = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(",")
S, N = 256, 60000; rng = np.random.default_rng(1)
def load(p):
    sp = plyload.load(p); i = np.nonzero(sp["opacity"] > 0.05)[0]; w = sp["opacity"][i]
    i = rng.choice(i, size=min(N, len(i)), replace=False, p=w / w.sum()); return {k: v[i] for k, v in sp.items()}
sps = {s: load(f"{plydir}/{s}.ply") for s in stages}
allp = np.concatenate([sp["pos"] for sp in sps.values()]); lo, hi = np.percentile(allp, 1, 0), np.percentile(allp, 99, 0)
ctr, rad = (lo + hi) / 2, np.linalg.norm(hi - lo) / 2
VIEW = np.array([float(v) for v in os.environ.get("VIEW", "-1,0,0").split(",")])   # registry view: the look direction
def shot(sp, deg):
    a = np.radians(deg); d = -VIEW; d = np.array([d[0] * np.cos(a) - d[2] * np.sin(a), 0, d[0] * np.sin(a) + d[2] * np.cos(a)])
    R, t = splat.look_at(ctr + d * rad * 2.6, ctr, up=(0, -1, 0))
    img, _ = splat.render(sp, R, t, S * 1.05, S, S, (0.02, 0.02, 0.025)); return (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1]
def tile(path):
    a = cv2.imread(path) if path and os.path.exists(path) else np.zeros((S, S, 3), np.uint8)
    h, w = a.shape[:2]; k = S / max(h, w); a = cv2.resize(a, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    o = np.zeros((S, S, 3), np.uint8); y, x = (S - a.shape[0]) // 2, (S - a.shape[1]) // 2; o[y:y + a.shape[0], x:x + a.shape[1]] = a; return o
cols = int(os.environ.get("COLS", 2)); rows = []
for k, s in enumerate(stages):
    n = int("".join(ch for ch in s if ch.isdigit()) or 0)
    row = np.hstack([tile(f"{trent}{n:02d}.png"), tile(f"{stilldir}/{s}.png"), shot(sps[s], 0), shot(sps[s], 35)])
    lab = np.zeros((22, row.shape[1], 3), np.uint8)
    for j, txt in enumerate(["Trent " + s, "ours: klein still", "ours: splat, front", "ours: splat, 35 deg"]):
        cv2.putText(lab, txt, (j * S + 6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 210, 210), 1)
    rows.append(np.vstack([row, lab]))
while len(rows) % cols: rows.append(np.zeros_like(rows[0]))
grid = np.vstack([np.hstack(rows[i:i + cols]) for i in range(0, len(rows), cols)])
cv2.imwrite(out, grid, [cv2.IMWRITE_JPEG_QUALITY, 86]); print(out, grid.shape)
