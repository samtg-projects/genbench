"""Task 1384, rock (Trent's branch 05): keep the rock immutable. klein repainted the rock's surface from stage 4 on, so each
stage here is the bare rock K00 with only its growth zone composited in: the zone is where the stages differ from K00
inside the zone box (the largest difference region across stages, dilated), feathered at its edge.
    rock_zone.py SRC_DIR OUT_DIR ZONE         reads K00..K10_seed_7.png, writes KNN.png and KNN-zone.png
ZONE is moss, lichen, fern, orchid or vine; every zone's stills are edits of the same bare rock K00."""
import sys, cv2, numpy as np
src, out, zone = sys.argv[1], sys.argv[2], sys.argv[3]
K = [cv2.imread(f"{src}/K{k:02d}_seed_7.png").astype(np.float32) for k in range(11)]
diff = [np.abs(k - K[0]).max(2) for k in K]
peak = np.maximum.reduce([(d > 60).astype(np.uint8) for d in diff[4:8]])                    # where the grown zone sits
peak = cv2.morphologyEx(peak, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(peak); big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
x, y, w, h = st[big, :4]; pad = int(0.25 * max(w, h))
box = np.zeros_like(peak); box[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 1
print(zone, "zone box", (x - pad, y - pad, w + 2 * pad, h + 2 * pad))
cv2.imwrite(f"{out}/K00.png", K[0].astype(np.uint8))
if zone == "vine":                                                     # a thin climber spread up the right edge: its whole side
    box[:] = 0; box[:, K[0].shape[1] // 2:] = 1
for k in range(1, 11):
    hsv = cv2.cvtColor(K[k].astype(np.uint8), cv2.COLOR_BGR2HSV); H = hsv[:, :, 0].astype(int)
    if zone == "vine":                                                 # its leaves only: greens, every blob (no main region)
        m = ((diff[k] > 40) & (box > 0) & (H >= 33) & (H <= 90) & (hsv[:, :, 1] > 50)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        dead = {8: 0.4, 9: 0.85, 10: 0.9}.get(k, 0)                       # klein's decay edits stayed green: age the leaves here
        if k == 10:                                                     # rest: only the lowest stems remain
            ys = np.nonzero(m)[0]; m[: int(np.percentile(ys, 70))] = 0 if len(ys) else m[:0]
        a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)[:, :, None]
        g = cv2.cvtColor(cv2.cvtColor(K[k].astype(np.uint8), cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR).astype(np.float32)
        leaf = K[k] * (1 - dead) + (g * 0.5 + np.array([45, 75, 110], np.float32) * 0.5) * dead
        o = K[0] * (1 - a) + leaf * a
        cv2.imwrite(f"{out}/K{k:02d}.png", o.astype(np.uint8)); cv2.imwrite(f"{out}/K{k:02d}-zone.png", (a[:, :, 0] * 255).astype(np.uint8))
        print(f"K{k:02d}", "zone px", int(m.sum())); continue
    lo, sat = (4, 80) if zone == "lichen" else (8, 60)                  # lichen: orange crusts and pale grey-greens too
    growth = ((H >= lo) & (H <= 95)) | (hsv[:, :, 1] < sat)            # greens, olives, browns, creams; not klein's pink/blue specks
    m = ((diff[k] > 40) & (box > 0) & growth).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:                                                          # the growth is one cushion: its main region (and any big pieces)
        big = st[1:, cv2.CC_STAT_AREA].max(); m = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 0.25 * big]).astype(np.uint8)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.5)[:, :, None]
    o = K[0] * (1 - a) + K[k] * a
    cv2.imwrite(f"{out}/K{k:02d}.png", o.astype(np.uint8)); cv2.imwrite(f"{out}/K{k:02d}-zone.png", (a[:, :, 0] * 255).astype(np.uint8))
    print(f"K{k:02d}", "zone px", int(m.sum()))
