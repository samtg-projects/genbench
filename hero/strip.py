"""Fixed-camera strip: front and side views of each PLY, y-down frame. Usage: strip.py OUT.png ply..."""
import sys, numpy as np, cv2
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import plyload, splat
import os; NOLINE = os.environ.get('NOLINE'); out = sys.argv[1]; W, H = int(os.environ.get('TILEW', 300)), 600
def thin(sp, n=140000):
    i = np.random.default_rng(0).permutation(np.nonzero(sp["opacity"] > 0.05)[0])[:n]; return {k: v[i] for k, v in sp.items()}
tiles = []
for p in sys.argv[2:]:
    sp = thin(plyload.load(p)); col = []
    for eye in ((0, 0, -5.2), (5.2, 0, 0)):          # front (camera at -z looking +z), side
        R, t = splat.look_at(eye, (0, 0, 0), up=(0, -1, 0))
        img, a = splat.render(sp, R, t, 1500, W, H, (0.06, 0.06, 0.07))
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1].copy()
        if not NOLINE: cv2.line(img, (W // 2, 0), (W // 2, H), (60, 60, 160), 1)     # fixed-camera centre line
        col.append(img)
    tiles.append(np.vstack(col))
cv2.imwrite(out, np.hstack(tiles))
