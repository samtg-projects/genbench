# Task 1357 pose sweep: per turn hypothesis, PSNR of the splat vs the video frame at its analytic pose (every 10th frame),
# plus a sheet: frame 0 / 60 / 120 from their poses, and an off-axis view (camera 90 deg past the end of the arc, 45 deg up).
import sys, json, math, tempfile, os
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api"))
import thumbnail_cpu as tc
from PIL import Image, ImageDraw
H = Path.home(); S = 352
jobs = [(kv.split(":") + ["10000", ""][len(kv.split(":")) - 2:])[:4] for kv in os.environ.get("JOBS", "30:35c67369,90:6b3414b2,180:3423d3c0,360:1cfc2636").split(",")]   # JOBS=turn:job[:step[:dataset]],...
def render(ply, c2w, fl):
    tf = {"w": S, "h": S, "fl_x": fl, "fl_y": fl, "cx": S / 2, "cy": S / 2, "frames": [{"transform_matrix": np.asarray(c2w).tolist()}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t: json.dump(tf, t)
    im = tc.render_thumbnail(Path(ply), Path(t.name), S, S, bg_color=(0.0, 0.0, 0.0)); os.unlink(t.name); return im
def look(c):
    f = -np.asarray(c, float); f /= np.linalg.norm(f); up = np.array([0, 0, 1.]); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    m = np.eye(4); m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = r, u, -f, c; return m
rows = []; print("turn  PSNR(mean over 13 frames)  splats")
for T, j, st, dn in jobs:
    ds = H / f"workcloud/data/nerfstudio/{dn or 'pathC-pose-t' + T}/dataset"; t = json.load(open(ds / "transforms.json"))
    ply = H / f"workcloud/outputs/nerfstudio/{j}/exports/export_{st}.ply"; fl = t["fl_x"] * S / t["w"]
    ps = []
    for k in range(0, 121, 10):
        fr = t["frames"][k]; gt = np.asarray(Image.open(ds / fr["file_path"]).convert("RGB").resize((S, S)), float) / 255
        pr = np.asarray(render(ply, fr["transform_matrix"], fl).convert("RGB"), float) / 255
        ps.append(-10 * math.log10(max(((gt - pr) ** 2).mean(), 1e-10)))
    nsp = int(open(ply, "rb").read(400).split(b"element vertex ")[1].split(b"\n")[0])
    print(f"{T:>4} @{st:>5}  {np.mean(ps):6.2f} dB  (min {min(ps):.2f}, max {max(ps):.2f})  {nsp}")
    tiles = [render(ply, t["frames"][k]["transform_matrix"], fl) for k in (0, 60, 120)]
    a = math.radians(float(T) + 90); e = math.radians(45); R = 3.0
    tiles.append(render(ply, look([R * math.cos(e) * math.cos(a), R * math.cos(e) * math.sin(a), R * math.sin(e)]), fl))
    row = Image.new("RGB", (4 * S, S))
    for i, im in enumerate(tiles):
        ImageDraw.Draw(im).text((6, 4), (f"{dn or 'turn ' + T} @{int(st)//1000}k: " if i == 0 else "") + ["frame 1", "frame 61", "frame 121", "off-axis +90, 45 up"][i], fill=(220, 220, 220)); row.paste(im, (i * S, 0))
    rows.append(row)
ds = H / "workcloud/data/nerfstudio/pathC-pose-t30/dataset"
gtrow = Image.new("RGB", (4 * S, S))
for i, k in enumerate((1, 61, 121)):
    im = Image.open(ds / f"images/f_{k:03d}.png").convert("RGB").resize((S, S)); ImageDraw.Draw(im).text((6, 4), f"video frame {k}", fill=(220, 220, 220)); gtrow.paste(im, (i * S, 0))
sheet = Image.new("RGB", (4 * S, (len(rows) + 1) * S)); sheet.paste(gtrow, (0, 0))
for i, r in enumerate(rows): sheet.paste(r, (0, (i + 1) * S))
sheet.save(H / os.environ.get("SHEET", "var/genbench/pathC/posesweep-sheet.jpg"), quality=90); print("sheet saved")
