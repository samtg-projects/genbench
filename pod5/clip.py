"""Task 1380: life-cycle clip from aligned stage PLYs, the way the player dissolves: each stage thinned to N splats,
a fixed random rank per splat, and over each crossfade window splats of A hand off to B in rank order.
Fixed camera with a slow +-12 deg sway. Usage: clip.py OUTDIR VIEW(x|-x|z|-z) ply... (holds below, Trent's)."""
import sys, os, numpy as np, cv2
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload, splat
out, view, plys = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out, exist_ok=True)
HOLD = [1.2, 1.2, 1.2, 1.5, 2.5, 3.5, 3.0, 1.6, 1.4, 1.4][:len(plys)]
FPS, W, H, N, XF = 24, 720, 720, 30000, 0.7
rng = np.random.default_rng(5)
S = []
for p in plys:
    sp = plyload.load(p); s = sp["scale"]            # importance-only thinning (task 1383): top N by opacity x projected area
    imp = sp["opacity"] * (s[:, 0]*s[:, 1] + s[:, 1]*s[:, 2] + s[:, 0]*s[:, 2]); i = np.argsort(-imp)[:N]
    sp = {k: v[i] for k, v in sp.items()}; sp["rank"] = rng.random(len(i)); S.append(sp)
t_edges = np.cumsum([0] + HOLD); T = t_edges[-1]
ax = {"x": (1, 0, 0), "-x": (-1, 0, 0), "z": (0, 0, 1), "-z": (0, 0, -1)}[view]
nf = int(round(T * FPS)); fr = int(os.environ.get("ONLY", -1))
for f in range(nf):
    if fr >= 0 and f != fr: continue
    t = f / FPS; k = min(np.searchsorted(t_edges, t, side="right") - 1, len(S) - 1)
    # crossfade into stage k+1 over the last XF seconds of stage k (loops back to stage 0 at the end)
    u = np.clip((t - (t_edges[k + 1] - XF)) / XF, 0, 1); a, b = S[k], S[(k + 1) % len(S)]
    sel_a = a["rank"] >= u; sel_b = b["rank"] < u
    sp = {key: np.concatenate([a[key][sel_a], b[key][sel_b]]) for key in ("pos", "axes", "scale", "color", "opacity")}
    ang = np.radians(12) * np.sin(2 * np.pi * t / T)
    d = np.array(ax, float); c, s_ = np.cos(ang), np.sin(ang)
    d = np.array([d[0] * c - d[2] * s_, 0, d[0] * s_ + d[2] * c])
    eye = np.array([0, 0.05, 0]) + d * 3.4
    R, tt = splat.look_at(eye, (0, 0.05, 0), up=(0, -1, 0))
    img, _ = splat.render(sp, R, tt, 1150, W, H, (0.03, 0.03, 0.035))
    cv2.imwrite(f"{out}/f{f:04d}.png", (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1])
print("frames", nf)
