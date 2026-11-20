"""Task 1384, rock: one row per zone, close up on that zone (aimed at its peak layer's centre, from the front and a little
above), stages 1 3 5 6 8 9 10, then the whole rock with every zone at its peak.
    zones_sheet.py OUT.jpg ALLDIR ZONEDIR...      (ZONEDIR/final/KNN.ply and zone/KNN.ply; ALLDIR/K06.ply)"""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload, splat
out, alldir, zones = sys.argv[1], sys.argv[2], sys.argv[3:]; S = 220; STAGES = (1, 3, 5, 6, 8, 9, 10); rows = []
def shot(sp, target, dist, f):
    d = np.array([1.0, -0.35, 0.0]); d /= np.linalg.norm(d)
    R, t = splat.look_at(target + d * dist, target, up=(0, -1, 0)); img, _ = splat.render(sp, R, t, f, S, S, (0.02, 0.02, 0.025))
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1]
def load(p):
    sp = plyload.load(p); i = np.nonzero(sp["opacity"] > 0.05)[0]; return {k: v[i] for k, v in sp.items()}
for z in zones:
    lay = plyload.load(f"{z}/final/zone/K06.ply"); tgt = np.median(lay["pos"], 0)
    tiles = [shot(load(f"{z}/final/K{k:02d}.ply"), tgt, 0.9, 330) for k in STAGES]
    row = np.hstack(tiles); cv2.putText(row, os.path.basename(z).replace("zone-", "").replace("rockc", "moss"), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
    rows.append(row)
a = load(f"{alldir}/K06.ply"); c = np.median(a["pos"][a["opacity"] > 0.3], 0)
whole = np.hstack([shot(load(f"{alldir}/K{k:02d}.ply"), c, 2.2, 300) for k in STAGES])
cv2.putText(whole, "all five zones", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1); rows.append(whole)
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 86]); print(out)
