# Task 1357: seed points round the origin for analytic-pose datasets (Brush's random init only fills the cameras' bounding box).
import sys, json, numpy as np
from pathlib import Path
d = Path(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 20000; r = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
rng = np.random.default_rng(0); p = rng.normal(size=(n, 3)); p /= np.linalg.norm(p, axis=1, keepdims=True); p *= r * rng.random((n, 1)) ** (1 / 3)
with open(d / "init.ply", "wb") as f:
    f.write(f"ply\nformat binary_little_endian 1.0\nelement vertex {n}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n".encode())
    rec = np.zeros(n, dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
    rec["x"], rec["y"], rec["z"] = p.T; rec["r"] = rec["g"] = rec["b"] = 128; f.write(rec.tobytes())
t = json.load(open(d / "transforms.json")); t["ply_file_path"] = "init.ply"; json.dump(t, open(d / "transforms.json", "w"), indent=1)
print("seeded", d, n, r)
