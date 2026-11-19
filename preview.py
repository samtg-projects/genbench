# Ticket 1114: preview TripoSplat PLYs with nerfstudio-api's torch-free thumbnailer, 4 views around the object.
import sys, json, math, tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api"))
import thumbnail_cpu as tc
from PIL import Image

def look_at(eye, target, up):
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    m = np.eye(4); m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = r, u, -f, eye    # OpenGL c2w
    return m

up_axis = sys.argv[1]            # "y", "-y" (TripoSplat is y-down) or "z"
out = Path(sys.argv[2]); plys = [Path(p) for p in sys.argv[3:]]
S = 320; rows = []
for ply in plys:
    c = tc._read_ply_float_columns(ply, ["x", "y", "z"])
    xyz = np.stack([c["x"], c["y"], c["z"]], -1)
    ctr = np.median(xyz, 0); rad = np.percentile(np.linalg.norm(xyz - ctr, axis=1), 98)
    up = {"y": np.array([0, 1, 0.]), "-y": np.array([0, -1, 0.]), "z": np.array([0, 0, 1.])}[up_axis]
    a1 = np.array([1, 0, 0.]); a2 = np.cross(up, a1)
    tiles = []
    for k in range(4):
        th = k * math.pi / 2; el = math.radians(15)
        d = math.cos(el) * (math.cos(th) * a2 + math.sin(th) * a1) + math.sin(el) * up
        f = S / 2 / math.tan(math.radians(20))
        tf = {"w": S, "h": S, "fl_x": f, "fl_y": f, "cx": S / 2, "cy": S / 2,
              "frames": [{"transform_matrix": look_at(ctr + d * rad / math.sin(math.radians(20)) * 1.1, ctr, up).tolist()}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump(tf, t)
        tiles.append(tc.render_thumbnail(ply, Path(t.name), S, S, bg_color=(0.0, 0.0, 0.0)))
    rows.append(tiles)
import os
ind = os.environ.get("INPUTS")
cols = 5 if ind else 4
sheet = Image.new("RGB", (cols * S, len(rows) * S))
for i, r in enumerate(rows):
    off = 0
    if ind:
        sheet.paste(Image.open(Path(ind) / (plys[i].stem + ".png")).convert("RGB").resize((S, S)), (0, i * S)); off = S
    for j, im in enumerate(r):
        sheet.paste(im, (off + j * S, i * S))
sheet.save(out); print("saved", out, len(rows), "rows")
