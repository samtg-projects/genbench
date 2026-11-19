"""Stem axis per stage: y-down PLYs. Bands along y from the stem base upward; centroid x,z of opaque splats per band."""
import sys, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import plyload
for p in sys.argv[1:]:
    sp = plyload.load(p); P = sp["pos"]; o = sp["opacity"] > 0.5
    y = P[:, 1]; base = np.percentile(y[o], 99.5); top = np.percentile(y[o], 0.5)
    H = base - top
    rows = []
    for f in np.linspace(0.02, 0.6, 12):
        yc = base - f * H; m = o & (np.abs(y - yc) < 0.02 * H)
        if m.sum() < 20: continue
        x, z = P[m, 0], P[m, 2]
        rows.append((f, np.median(x), np.median(z), np.percentile(x, 90) - np.percentile(x, 10), m.sum()))
    r = np.array(rows)
    print(p.split("/")[-1], f"base y {base:.3f} top {top:.3f} H {H:.3f}")
    for f, x, z, w, n in r: print(f"  f={f:.2f} x={x:+.4f} z={z:+.4f} width={w:.4f} n={int(n)}")
