"""Balanced thinning (task 1383, a=0.5 approved): keep N splats. Voxelise the stage (cell C metres in the PLY's frame), give each
occupied cell a quota proportional to (its summed importance)^ALPHA, keep the top-importance splats per cell; importance = opacity x
projected area (s1 s2 + s2 s3 + s1 s3). Writes a 3DGS PLY with every input property kept (same layout), rows subset.
Usage: thin_balanced.py IN.ply OUT.ply [N=30000] [ALPHA=0.5] [C=0.04]"""
import sys, numpy as np
inp, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 30000; ALPHA = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
C = float(sys.argv[5]) if len(sys.argv) > 5 else 0.04
with open(inp, "rb") as f:
    head = b""; names = []; n = 0
    while True:
        line = f.readline(); head += line; t = line.decode().strip()
        if t.startswith("element vertex"): n = int(t.split()[-1])
        elif t.startswith("property"):
            assert t.split()[1] == "float", "float properties only"; names.append(t.split()[-1])
        elif t == "end_header": break
    data = np.frombuffer(f.read(n * 4 * len(names)), dtype="<f4").reshape(n, len(names))
c = {k: data[:, i].astype(np.float64) for i, k in enumerate(names)}
op = 1 / (1 + np.exp(-c["opacity"])); s = np.exp(np.stack([c["scale_0"], c["scale_1"], c["scale_2"]], 1))
imp = op * (s[:, 0]*s[:, 1] + s[:, 1]*s[:, 2] + s[:, 0]*s[:, 2])
if N >= n: keep = np.arange(n)
else:
    key = np.floor(np.stack([c["x"], c["y"], c["z"]], 1) / C).astype(np.int64)
    _, cell = np.unique(key, axis=0, return_inverse=True); cell = cell.ravel()
    q = np.bincount(cell, imp) ** ALPHA; q = q / q.sum() * N
    order = np.lexsort((-imp, cell)); starts = np.r_[0, np.cumsum(np.bincount(cell))[:-1]]
    rank = np.empty(n, np.int64); rank[order] = np.arange(n) - starts[cell[order]]
    keep = np.nonzero(rank < np.maximum(1, np.round(q[cell])).astype(int))[0]
    if len(keep) > N: keep = keep[np.argsort(-imp[keep])[:N]]
    elif len(keep) < N:                                  # top up by importance to exactly N
        rest = np.setdiff1d(np.arange(n), keep); keep = np.concatenate([keep, rest[np.argsort(-imp[rest])[:N - len(keep)]]])
keep = np.sort(keep)
with open(out, "wb") as f:
    f.write(head.replace(f"element vertex {n}".encode(), f"element vertex {len(keep)}".encode(), 1)); f.write(data[keep].tobytes())
print(out, len(keep), "of", n)
