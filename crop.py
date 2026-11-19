# crop.py in.ply out.ply frac : keep splats within the given fraction of the shell radius around the centre
import sys, numpy as np
src, dst, frac = sys.argv[1], sys.argv[2], float(sys.argv[3])
raw = open(src, "rb").read(); end = raw.index(b"end_header\n") + len(b"end_header\n")
head = raw[:end].decode().splitlines()
props = [l.split()[2] for l in head if l.startswith("property float")]
n = int([l for l in head if l.startswith("element vertex")][0].split()[2])
a = np.frombuffer(raw[end:end + n * 4 * len(props)], dtype=np.dtype([(p, "<f4") for p in props]))
xyz = np.stack([a["x"], a["y"], a["z"]], 1)
c = np.median(xyz, 0); d = np.linalg.norm(xyz - c, axis=1)
R = np.percentile(d, 95)
keep = d < frac * R
print("n", n, "centre", c.round(3), "p50/p95 dist", np.percentile(d, 50).round(3), R.round(3), "kept", int(keep.sum()))
out = "\n".join(l if not l.startswith("element vertex") else f"element vertex {int(keep.sum())}" for l in head) + "\n"
open(dst, "wb").write(out.encode() + a[keep].tobytes())
