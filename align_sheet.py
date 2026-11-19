# Task 1361: before/after sheet for the plane alignment. Rows = stages; columns = before front, before side, after front, after side.
import sys, math
from pathlib import Path
import numpy as np
sys.argv = [sys.argv[0], "test"] + sys.argv[1:]   # reuse wip.py's renderer without running a mode
exec(open(Path(__file__).parent / "wip.py").read().split("mode = sys.argv[1]")[0])
before, after, out = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
up = [0, -1, 0]; S = 256; plys = sorted(p.name for p in before.glob("S[0-9][0-9].ply"))
ctr, rad = frame_of(before / plys[0])
sheet = Image.new("RGB", (4 * S, len(plys) * S))
for i, nm in enumerate(plys):
    for j, (d, th, tag) in enumerate([(before, math.pi / 2, "before front"), (before, 0, "before side"), (after, math.pi / 2, "aligned front"), (after, 0, "aligned side")]):
        sheet.paste(label(render(d / nm, orbit(ctr, rad, up, th, 5), S), f"{nm[:3]} {tag}"), (j * S, i * S))
sheet.save(out, quality=88); print("saved", out)
