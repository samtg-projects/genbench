"""Task 1384: a life-cycle clip from registered stage PLYs, the way the player dissolves (claude-wafer's pod5/clip.py, with
holds as an argument and the frames rendered across processes). Each stage is thinned to N splats with a fixed random
rank; over each crossfade, splats of A hand off to B in rank order. Fixed camera with a slow +-12 deg sway.
    clip.py OUT.mp4 HOLDS ply...       HOLDS: comma list of seconds, or one number for every stage"""
import sys, os, subprocess, tempfile, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload, splat
out, holds, plys = sys.argv[1], sys.argv[2], sys.argv[3:]
HOLD = [float(h) for h in holds.split(",")] if "," in holds else [float(holds)] * len(plys)
FPS, W, H, N, XF = 24, 640, 640, 30000, min(0.7, 0.5 * min(HOLD))
VIEW = np.array([float(v) for v in os.environ.get("VIEW", "-1,0,0").split(",")]); DIST = float(os.environ.get("DIST", 3.4))
rng = np.random.default_rng(5); S = []
for p in plys:
    sp = plyload.load(p); i = np.nonzero(sp["opacity"] > 0.05)[0]
    w = sp["opacity"][i]; i = rng.choice(i, size=min(N, len(i)), replace=False, p=w / w.sum())
    sp = {k: v[i] for k, v in sp.items()}; sp["rank"] = rng.random(len(i)); S.append(sp)
allp = np.concatenate([s["pos"] for s in S]); ctr = (np.percentile(allp, 2, 0) + np.percentile(allp, 98, 0)) / 2
t_edges = np.cumsum([0] + HOLD); T = t_edges[-1]; nf = int(round(T * FPS)); tmp = tempfile.mkdtemp(prefix="clip-")
def frame(f):
    t = f / FPS; k = min(np.searchsorted(t_edges, t, side="right") - 1, len(S) - 1)
    u = np.clip((t - (t_edges[k + 1] - XF)) / XF, 0, 1); a, b = S[k], S[(k + 1) % len(S)]
    sp = {key: np.concatenate([a[key][a["rank"] >= u], b[key][b["rank"] < u]]) for key in ("pos", "axes", "scale", "color", "opacity")}
    ang = np.radians(12) * np.sin(2 * np.pi * t / T); d = -VIEW; c, s_ = np.cos(ang), np.sin(ang)
    d = np.array([d[0] * c - d[2] * s_, 0, d[0] * s_ + d[2] * c])
    R, tt = splat.look_at(ctr + d * DIST * 0.5, ctr, up=(0, -1, 0))
    img, _ = splat.render(sp, R, tt, 1000 * W / 720, W, H, (0.03, 0.03, 0.035))
    cv2.imwrite(f"{tmp}/f{f:04d}.png", (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1])
if __name__ != "__main__":
    sys.exit(0)
import multiprocessing as mp
with mp.get_context("fork").Pool(int(os.environ.get("PROCS", 8))) as pool: pool.map(frame, range(nf))
subprocess.run(["/opt/homebrew/bin/ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png", "-c:v", "libx264",
                "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
print(out, nf, "frames", round(T, 1), "s")
