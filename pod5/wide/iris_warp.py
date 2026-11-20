"""Task 1384, iris (Trent's branch 06): pupil frames by radial warp of one klein still, so the iris pattern is identical in
every frame. The pupil grows or shrinks about the iris centre; the outer edge stays fixed (as a real iris does).
Light frames (04 warm, 08 cool) are klein edits at a medium pupil and are warped to the same pupil as the neutral still.
    iris_warp.py SRC_DIR OUT_DIR       reads I00/I04/I08_seed_7.png, writes I01..I10.png"""
import sys, cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
def geom(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); H, W = g.shape
    disc = (g > 18).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(disc)
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); ys, xs = np.nonzero(lab == k)
    cx, cy = xs.mean(), ys.mean(); R = np.sqrt((lab == k).sum() / np.pi + 0.0)
    # pupil: the dark blob at the centre
    dark = (g < 30).astype(np.uint8); dark[lab != k] = 0
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - cx, yy - cy)
    filled = cv2.morphologyEx(((g < 30) & (r < 0.6 * R)).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(filled)
    j = min(range(1, n2), key=lambda i: np.hypot(*(np.array(np.nonzero(lab2 == i))[::-1].mean(1) - [cx, cy])))
    p = np.sqrt(st2[j, cv2.CC_STAT_AREA] / np.pi)
    # outer radius from the disc's area (the disc includes the pupil hole, so add it back)
    R = np.sqrt(((lab == k).sum() + st2[j, cv2.CC_STAT_AREA]) / np.pi)
    return cx, cy, p, R
def warp(img, cx, cy, p0, R, p1, dx=0.0):
    """Output radius r maps from source radius s: pupil p1->p0, edge R->R, linear in between; outside R unchanged."""
    H, W = img.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    X, Y = xx - (cx + dx), yy - cy; r = np.hypot(X, Y) + 1e-6
    s = np.where(r < p1, r * p0 / p1, p0 + (r - p1) * (R - p0) / (R - p1)); s = np.where(r > R, r, s)
    mx, my = (cx + X * s / r).astype(np.float32), (cy + Y * s / r).astype(np.float32)
    o = cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    o[r < p1 * 0.995] = 0                                    # the pupil stays pure black
    return o
I0 = cv2.imread(f"{src}/I00_seed_7.png"); cx, cy, p0, R = geom(I0); print("iris centre", round(cx), round(cy), "pupil", round(p0), "edge", round(R))
plan = {1: (I0, 1.0, 0), 2: (I0, 0.82, 0), 3: (I0, 0.6, 0), 4: ("I04", 1.0, 0), 5: (I0, 1.0, 0), 6: (I0, 1.2, 0), 7: (I0, 1.75, 0),
        8: ("I08", 1.0, 0), 9: (I0, 1.0, -0.035 * R), 10: (I0, 1.0, 0)}
for k, (im, f, dx) in plan.items():
    if isinstance(im, str):
        im = cv2.imread(f"{src}/{im}_seed_7.png"); c = geom(im); im = warp(im, c[0], c[1], c[2], c[3], p0)   # its own pupil to p0
        if abs(c[0] - cx) > 4 or abs(c[1] - cy) > 4: print("light frame off centre", k, c)
    o = warp(im, cx, cy, p0, R, p0 * f, dx)
    cv2.imwrite(f"{out}/I{k:02d}.png", o); print(f"I{k:02d} pupil x{f}", "shift" if dx else "")
