# Task 1361: per-stage extents, to check the stages share scale (y-down: the mound base is at max y).
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api")); import thumbnail_cpu as tc
for f in sys.argv[1:]:
    c = tc._read_ply_float_columns(Path(f), ["x", "y", "z", "opacity"]); m = c["opacity"] > 0
    x, y, z = c["x"][m], c["y"][m], c["z"][m]; base = y > np.percentile(y, 60)
    p = lambda a: np.percentile(a, [2, 98]).round(3)
    print(Path(f).stem, "all y", p(y), "| base band x", p(x[base]), "z", p(z[base]), "centre", np.round([np.median(x[base]), np.median(z[base])], 3))
