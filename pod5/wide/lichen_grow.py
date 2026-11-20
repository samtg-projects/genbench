"""Task 1384, rock: the lichen zone. klein drew the whole lichen patch by stage 3 and then barely changed it (and repainted
the rock), so the stages are made from one peak still instead: the patch (pale grey-green rosettes, the orange crust between
them) is taken off the bare rock K00 and revealed over a growing radius from its left edge, as lichen spreads; then it fades,
browns and shrinks for ageing, decay and rest. Each stage is K00 with the patch composited in, like rock_zone.py.
    lichen_grow.py SRC_DIR OUT_DIR PEAK      (PEAK: the still to take the patch from, e.g. K06)"""
import sys, cv2, numpy as np
src, out, peak = sys.argv[1], sys.argv[2], sys.argv[3]
K0 = cv2.imread(f"{src}/K00_seed_7.png").astype(np.float32); P = cv2.imread(f"{src}/{peak}_seed_7.png").astype(np.float32)
hsv = cv2.cvtColor(P.astype(np.uint8), cv2.COLOR_BGR2HSV); H, S, V = [hsv[:, :, i].astype(int) for i in range(3)]
rosette = (H >= 60) & (H <= 112) & (S >= 12) & (S <= 120) & (V > 70)                    # the pale grey-green rosettes
m = (rosette & (np.abs(P - K0).max(2) > 35)).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m); big = st[1:, cv2.CC_STAT_AREA].max()
m = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 0.05 * big]).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))                   # take the crust between the rosettes too
# spread from the patch's left edge (klein drew the rosettes as a ring, so its centre is bare): the leftmost rosettes' middle
ys, xs = np.nonzero(m); left = xs < np.percentile(xs, 4); cx, cy = xs[left].mean(), ys[left].mean()
R = np.percentile(np.hypot(xs - cx, ys - cy), 99)
print("patch centre", int(cx), int(cy), "radius", int(R), "px", int(m.sum()))
yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]; r = np.hypot(xx - cx, yy - cy)
# stage: (reveal radius as a fraction of R, colour: 0 fresh .. 1 dead)
PLAN = [(0.12, 0), (0.22, 0), (0.36, 0), (0.55, 0), (0.78, 0), (1.0, 0), (1.0, 0), (1.0, 0.35), (0.85, 0.8), (0.3, 0.9)]
grey = cv2.cvtColor(cv2.cvtColor(P.astype(np.uint8), cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR).astype(np.float32)
brown = np.array([60, 85, 110], np.float32)                                               # BGR dull brown-grey
cv2.imwrite(f"{out}/K00.png", K0.astype(np.uint8))
for k, (f, dead) in enumerate(PLAN, 1):
    reveal = np.clip((f * R - r) / (0.08 * R) + 0.5, 0, 1)                                 # soft-edged disc of radius f R
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.0) * reveal
    col = P * (1 - dead) + (grey * 0.55 + brown * 0.45) * dead                              # ageing: desaturate toward brown-grey
    col = col * (1 - 0.25 * dead)
    o = K0 * (1 - a[:, :, None]) + col * a[:, :, None]
    cv2.imwrite(f"{out}/K{k:02d}.png", o.astype(np.uint8)); cv2.imwrite(f"{out}/K{k:02d}-zone.png", (a * 255).astype(np.uint8))
