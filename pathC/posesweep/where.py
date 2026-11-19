import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api")); import thumbnail_cpu as tc
for f in sys.argv[2:]:
    c = tc._read_ply_float_columns(Path(f), ["x", "y", "z", "opacity"]); xyz = np.stack([c["x"], c["y"], c["z"]], -1)
    print(Path(f).name, "n", len(xyz), "min", xyz.min(0).round(2), "max", xyz.max(0).round(2), "median |p|", np.median(np.linalg.norm(xyz, axis=1)).round(2), "opacity(logit) median", np.median(c["opacity"]).round(2))
t = json.load(open(sys.argv[1])); P = np.array([fr["transform_matrix"] for fr in t["frames"]])
print("camera centres: min", P[:, :3, 3].min(0).round(2), "max", P[:, :3, 3].max(0).round(2))
fwd = -P[:, :3, 2]; print("cam 0 forward", fwd[0].round(3), " points at origin?", (np.dot(fwd[0], -P[0, :3, 3]) / np.linalg.norm(P[0, :3, 3])).round(3))
