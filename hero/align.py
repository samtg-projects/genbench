"""Hero rose v2 (task 1376): stem-anchored alignment of the six TripoSplat stages (y-down frame).
Per stage: fit the stem centreline below the head, rotate about the stem base so the stem is vertical,
move the base to (0, BASE_Y, 0), straighten residual bend below the head, then optional stem thinning
(xz squeeze about the axis, below the head) and head scale (about the head's base).
Usage: align.py OUTDIR  (reads dl/six/<id>.ply, writes OUTDIR/<name>.ply and OUTDIR/align.json)"""
import sys, json, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import plyload
STAGES = [  # id, name, stem squeeze, head scale
    ("2632", "s1-bud",     0.60, 1.18),
    ("2634", "s2-opening", 0.58, 1.08),
    ("2635", "s3-bloom",   1.0, 1.0),
    ("2636", "s4-blown",   1.0, 1.0),
    ("2637", "s5-wilt",    0.75, 1.0),
    ("2639", "s6-dried",   1.0, 1.0),
]
BASE_Y = 0.47
out = sys.argv[1]; log = []

def apply_linear(sp, sel, M):
    """x -> M x for positions (already done by caller) and covariances of splats in sel."""
    A = sp["axes"][sel] * sp["scale"][sel][:, :, None]     # rows = scaled axes
    S = np.einsum("nki,nkj->nij", A, A)
    S = M @ S @ np.swapaxes(M, -1, -2)
    w, v = np.linalg.eigh(S)
    sp["scale"][sel] = np.sqrt(np.clip(w, 1e-14, None))
    sp["axes"][sel] = np.swapaxes(v, 1, 2)

def centreline(P, o, base, H, f0, f1):
    rows = []
    for f in np.linspace(f0, f1, 24):
        yc = base - f * H; m = o & (np.abs(P[:, 1] - yc) < 0.015 * H)
        if m.sum() > 30: rows.append((yc, np.median(P[m, 0]), np.median(P[m, 2]), np.percentile(P[m, 0], 90) - np.percentile(P[m, 0], 10)))
    return np.array(rows)

for sid, name, squeeze, hscale in STAGES:
    sp = plyload.load(f"dl/six/{sid}.ply"); P = sp["pos"]; o = sp["opacity"] > 0.5
    base = np.percentile(P[o, 1], 99.5); H = base - np.percentile(P[o, 1], 0.5)
    c = centreline(P, o, base, H, 0.02, 0.6)
    # head starts where the band width jumps past 3x the stem's median width
    sw = np.median(c[:8, 3]); jump = np.nonzero(c[:, 3] > 3 * sw)[0]
    yh = c[jump[0], 0] if len(jump) else base - 0.45 * H
    fh = (base - yh) / H
    st = c[(c[:, 0] > yh + 0.03 * H) & (c[:, 3] < 2 * sw)]
    # line fit x(y), z(y) on the stem
    ax = np.polyfit(st[:, 0], st[:, 1], 1); az = np.polyfit(st[:, 0], st[:, 2], 1)
    pb = np.array([np.polyval(ax, base), base, np.polyval(az, base)])   # stem base point
    d = np.array([-ax[0], -1.0, -az[0]]); d /= np.linalg.norm(d)        # up the stem (y-down → -y)
    tgt = np.array([0, -1.0, 0]); v = np.cross(d, tgt); s = np.linalg.norm(v); cth = d @ tgt
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + K + K @ K * ((1 - cth) / s**2) if s > 1e-9 else np.eye(3)
    tilt = np.degrees(np.arccos(np.clip(cth, -1, 1)))
    P[:] = (P - pb) @ R.T + np.array([0, BASE_Y, 0]); apply_linear(sp, slice(None), R[None])
    yh2 = BASE_Y - fh * H
    # residual bend: per-height offset of the stem centreline, faded to 0 entering the head
    c2 = centreline(P, o, BASE_Y, H, 0.02, fh - 0.02)
    c2 = c2[c2[:, 3] < 2 * sw]
    order = np.argsort(c2[:, 0])
    fade = np.clip((P[:, 1] - yh2) / (0.06 * H), 0, 1)        # 1 well below the head, 0 at/above it
    yl = np.clip(P[:, 1], c2[:, 0].min(), c2[:, 0].max())        # smooth cubic centreline, held flat past its ends
    ox = np.polyval(np.polyfit(c2[:, 0], c2[:, 1], 3), yl); oz = np.polyval(np.polyfit(c2[:, 0], c2[:, 2], 3), yl)
    P[:, 0] -= ox * fade; P[:, 2] -= oz * fade
    # stem thinning: squeeze xz toward the axis below the head, fading out over the sepals
    if squeeze != 1.0:
        k = 1 - (1 - squeeze) * fade
        sel = fade > 0
        P[sel, 0] *= k[sel]; P[sel, 2] *= k[sel]
        for kk in np.unique(np.round(k[sel], 2)):
            m = np.nonzero(sel)[0][np.round(k[sel], 2) == kk]
            apply_linear(sp, m, np.diag([kk, 1, kk])[None])
    # head scale about the head base point on the axis; blend in over the sepals
    if hscale != 1.0:
        g = 1 + (hscale - 1) * (1 - fade)
        piv = np.array([0, yh2, 0])
        P[:] = piv + (P - piv) * g[:, None]
        for gg in np.unique(np.round(g, 2)):
            m = np.nonzero(np.round(g, 2) == gg)[0]
            apply_linear(sp, m, np.eye(3)[None] * gg)
    plyload.save(f"{out}/{name}.ply", sp)
    log.append(dict(stage=name, source_file=int(sid), tilt_deg=round(float(tilt), 2), base_shift=[round(float(x), 4) for x in (np.array([0, BASE_Y, 0]) - pb)],
                    head_start_frac=round(float(fh), 3), stem_squeeze=squeeze, head_scale=hscale))
    print(log[-1])
json.dump(log, open(f"{out}/align.json", "w"), indent=1)
