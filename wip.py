# wip.py: process videos for doc 660 (ticket 1114) with nerfstudio-api's torch-free point renderer.
#   wip.py test <ply> <up x,y,z> <out.jpg>                       four orbit angles at 25 deg elevation
#   wip.py life25 <inputs> <prepared> <plys> <up> <outdir>       per stage: still | background removed | turning splat
#   wip.py rig <dataset> <ply> <outdir> [step]                     each Blender view beside the splat from the same pose
#   wip.py progress <plydir> <up> <outdir>                         Brush checkpoints in order, turning slowly
import sys, json, math, tempfile, os
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api"))
import thumbnail_cpu as tc
from PIL import Image, ImageDraw

def look_at(eye, target, up):
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    m = np.eye(4); m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = r, u, -f, eye
    return m

def render(ply, c2w, S, fl=None):
    f = fl or S / 2 / math.tan(math.radians(20))
    tf = {"w": S, "h": S, "fl_x": f, "fl_y": f, "cx": S / 2, "cy": S / 2, "frames": [{"transform_matrix": np.asarray(c2w).tolist()}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        json.dump(tf, t)
    im = tc.render_thumbnail(Path(ply), Path(t.name), S, S, bg_color=(0.0, 0.0, 0.0)); os.unlink(t.name)
    return im

def frame_of(ply):
    c = tc._read_ply_float_columns(Path(ply), ["x", "y", "z"])
    xyz = np.stack([c["x"], c["y"], c["z"]], -1)
    ctr = np.median(xyz, 0); rad = np.percentile(np.linalg.norm(xyz - ctr, axis=1), 98)
    return ctr, rad

def orbit(ctr, rad, up, th, el=25):
    up = np.asarray(up, float); a1 = np.array([1, 0, 0.]) if abs(up[0]) < .9 else np.array([0, 1, 0.])
    a1 = a1 - up * (a1 @ up); a1 /= np.linalg.norm(a1); a2 = np.cross(up, a1)
    e = math.radians(el)
    d = math.cos(e) * (math.cos(th) * a2 + math.sin(th) * a1) + math.sin(e) * up
    return look_at(ctr + d * rad / math.sin(math.radians(20)) * 1.15, ctr, up)

def label(im, text):
    ImageDraw.Draw(im).text((8, 6), text, fill=(200, 200, 200)); return im

mode = sys.argv[1]
if mode == "test":
    ply, up, out = sys.argv[2], [float(v) for v in sys.argv[3].split(",")], sys.argv[4]
    ctr, rad = frame_of(ply); S = 320
    sheet = Image.new("RGB", (4 * S, S))
    for k in range(4): sheet.paste(render(ply, orbit(ctr, rad, up, k * math.pi / 2), S), (k * S, 0))
    sheet.save(out); print("saved", out)
elif mode == "life25":
    ind, prep, plyd, up, outd = Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), [float(v) for v in sys.argv[5].split(",")], Path(sys.argv[6])
    outd.mkdir(parents=True, exist_ok=True); S = 480; F = int(os.environ.get("F", "18"))
    plys = sorted(plyd.glob("L[0-9][0-9].ply")); n = 0
    ctr, rad = frame_of(plys[len(plys) // 2])                      # one frame for all stages, so the sequence doesn't jump
    for i, ply in enumerate(plys):
        a = Image.open(ind / (ply.stem + ".png")).convert("RGB").resize((S, S))
        b = Image.open(prep / (ply.stem + "-prepared.webp")).convert("RGBA").resize((S, S))
        bb = Image.new("RGB", (S, S), (0, 0, 0)); bb.paste(b, (0, 0), b)
        for j in range(F):
            th = 2 * math.pi * (i * F + j) / (len(plys) * F) * 2
            fr = Image.new("RGB", (3 * S, S))
            fr.paste(label(a.copy(), f"{ply.stem}  FLUX.2 klein still"), (0, 0))
            fr.paste(label(bb.copy(), "background removed (BiRefNet)"), (S, 0))
            fr.paste(label(render(ply, orbit(ctr, rad, up, th), S), "TripoSplat: 262,144 Gaussians"), (2 * S, 0))
            fr.save(outd / f"f{n:05d}.jpg", quality=90); n += 1
    print("frames", n)
elif mode == "rig":
    ds, ply, outd = Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]); step = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    outd.mkdir(parents=True, exist_ok=True)
    t = json.load(open(ds / "transforms.json")); S = 512; fl = t["fl_x"] * S / t["w"]; n = 0
    for k, fr in enumerate(t["frames"][::step]):
        a = Image.open(ds / fr["file_path"]).convert("RGBA").resize((S, S))
        bg = Image.new("RGB", (S, S), (0, 0, 0)); bg.paste(a, (0, 0), a)
        im = Image.new("RGB", (2 * S, S))
        im.paste(label(bg, f"Blender Cycles view {k * step + 1}/{len(t['frames'])}"), (0, 0))
        im.paste(label(render(ply, fr["transform_matrix"], S, fl), "Brush splat, same camera"), (S, 0))
        im.save(outd / f"f{n:05d}.jpg", quality=90); n += 1
    print("frames", n)
elif mode == "progress":
    plyd, up, outd = Path(sys.argv[2]), [float(v) for v in sys.argv[3].split(",")], Path(sys.argv[4])
    outd.mkdir(parents=True, exist_ok=True); S = 640; F = int(os.environ.get("F", "12"))
    plys = sorted(plyd.glob("export_*.ply")); ctr, rad = frame_of(plys[-1]); n = 0
    for i, ply in enumerate(plys):
        nsp = int(open(ply, "rb").read(400).split(b"element vertex ")[1].split(b"\n")[0])
        for j in range(F):
            th = 2 * math.pi * (i * F + j) / (len(plys) * F)
            im = label(render(ply, orbit(ctr, rad, up, th, 30), S), f"Brush step {int(ply.stem.split('_')[1]):,} / 30,000   {nsp:,} splats")
            im.save(outd / f"f{n:05d}.jpg", quality=90); n += 1
    print("frames", n)
