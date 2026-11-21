"""Preview renders of a TripoSplat PLY with nerfstudio-api's torch-free thumbnailer (y-down; the input image's view is from +x)."""
import json, math, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image

_tc = None


def _thumb():
    global _tc
    if _tc is None:
        sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api"))
        import thumbnail_cpu
        _tc = thumbnail_cpu
    return _tc


UP = np.array([0, -1, 0.])


def _look_at(eye, target, up):
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    m = np.eye(4); m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = r, u, -f, eye
    return m


def _frame(ply):
    tc = _thumb()
    c = tc._read_ply_float_columns(ply, ["x", "y", "z"])
    xyz = np.stack([c["x"], c["y"], c["z"]], -1)
    ctr = np.median(xyz, 0)
    return ctr, np.percentile(np.linalg.norm(xyz - ctr, axis=1), 98)


def _shot(ply, ctr, rad, th, el, size, bg):
    d = math.cos(el) * (math.cos(th) * np.array([1, 0, 0.]) + math.sin(th) * np.array([0, 0, 1.])) + math.sin(el) * UP
    f = size / 2 / math.tan(math.radians(20))
    tf = {"w": size, "h": size, "fl_x": f, "fl_y": f, "cx": size / 2, "cy": size / 2,
          "frames": [{"transform_matrix": _look_at(ctr + d * rad / math.sin(math.radians(20)) * 1.05, ctr, UP).tolist()}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        json.dump(tf, t)
    return _thumb().render_thumbnail(ply, Path(t.name), size, size, bg_color=bg)


def beauty(ply: Path, work: Path):
    ctr, rad = _frame(ply)
    out = work / (ply.stem + "-beauty.png")
    _shot(ply, ctr, rad, math.radians(25), math.radians(12), 1024, (0.06, 0.06, 0.08)).save(out)
    return out


def sheet(ply: Path, work: Path, size=384):
    ctr, rad = _frame(ply)
    tiles = [_shot(ply, ctr, rad, k * math.pi / 2, math.radians(15), size, (0, 0, 0)) for k in range(4)]
    im = Image.new("RGB", (4 * size, size))
    for i, t in enumerate(tiles): im.paste(t, (i * size, 0))
    out = work / (ply.stem + "-sheet.jpg"); im.save(out, quality=90)
    return out
