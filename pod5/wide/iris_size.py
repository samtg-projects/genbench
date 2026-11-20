"""Task 1384, iris: after iris_norm.py, make every stage's disc the same size as seen from the front. The rim is measured
on the rendered silhouette (the outer contour's area, hole filled), and each stage is scaled about the disc centre.
    iris_size.py RADIUS ply...   (in place)"""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload, splat
rad, ps = float(sys.argv[1]), sys.argv[2:]; c = np.array([0, 0.47 - rad, 0]); S, F = 384, 384 * 1.6
R, t = splat.look_at(c + np.array([3.0, 0, 0]), c, up=(0, -1, 0))
def rim(sp):
    s2 = dict(sp); s2["color"] = np.ones_like(sp["color"]); img, _ = splat.render(s2, R, t, F, S, S, (0, 0, 0))
    m = (img[:, :, 0] > 0.5).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return np.sqrt(cv2.contourArea(max(cs, key=cv2.contourArea)) / np.pi) * 3.0 / F     # pixels -> scene units at distance 3
for p in ps:
    sp = plyload.load(p); keep = sp["opacity"] > 0.05; sub = {k: v[keep] for k, v in sp.items()}
    for _ in range(2):
        g = rad / rim(sub)
        for x in (sp, sub): x["pos"] = c + (x["pos"] - c) * g; x["scale"] *= g
    plyload.save(p, sp); print(os.path.basename(p), "rim now", round(float(rim(sub)), 3))
