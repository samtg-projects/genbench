"""One line per stage: stem tilt (deg), base x/z, stem width, head start fraction. Usage: survey.py ply..."""
import sys, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import plyload
def cl(P, o, base, H, f0, f1, n=24):
    r = []
    for f in np.linspace(f0, f1, n):
        yc = base - f * H; m = o & (np.abs(P[:, 1] - yc) < 0.015 * H)
        if m.sum() > 30: r.append((yc, np.median(P[m, 0]), np.median(P[m, 2]), np.percentile(P[m, 0], 90) - np.percentile(P[m, 0], 10)))
    return np.array(r)
for p in sys.argv[1:]:
    sp = plyload.load(p); P = sp["pos"]; o = sp["opacity"] > 0.5
    base = np.percentile(P[o, 1], 99.5); H = base - np.percentile(P[o, 1], 0.5)
    c = cl(P, o, base, H, 0.02, 0.7); sw = np.median(c[:8, 3]); j = np.nonzero(c[:, 3] > 3 * sw)[0]
    fh = (base - c[j[0], 0]) / H if len(j) else np.nan
    st = c[(c[:, 0] > base - (fh - 0.03) * H) & (c[:, 3] < 2 * sw)]
    ax = np.polyfit(st[:, 0], st[:, 1], 1); az = np.polyfit(st[:, 0], st[:, 2], 1)
    tilt = np.degrees(np.arctan(np.hypot(ax[0], az[0])))
    print(f"{p.split('/')[-1][:-4]} H={H:.3f} tilt={tilt:5.1f} base=({np.polyval(ax, base):+.3f},{np.polyval(az, base):+.3f}) stemW={sw:.4f} headf={fh:.2f} nstem={len(st)}")
