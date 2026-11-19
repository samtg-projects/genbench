"""Load a 3DGS PLY (Brush export) into the renderer's splat dict. Properties are read by name:
Brush writes f_rest_* in lexicographic order, so positional parsing would scramble SH."""
import numpy as np

C0 = 0.28209479177387814


def load(path):
    with open(path, "rb") as f:
        names, n = [], 0
        while True:
            line = f.readline().decode().strip()
            if line.startswith("element vertex"):
                n = int(line.split()[-1])
            elif line.startswith("property"):
                names.append(line.split()[-1])
            elif line == "end_header":
                break
        data = np.frombuffer(f.read(n * 4 * len(names)), dtype="<f4").reshape(n, len(names))
    c = {k: data[:, i] for i, k in enumerate(names)}
    pos = np.stack([c["x"], c["y"], c["z"]], 1).astype(float)
    q = np.stack([c["rot_0"], c["rot_1"], c["rot_2"], c["rot_3"]], 1).astype(float)  # w x y z
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    w, x, y, z = q.T
    Rm = np.stack([
        np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], 1),
        np.stack([2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)], 1),
        np.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], 1)], 1)
    axes = Rm.transpose(0, 2, 1)          # rows = local axes in world
    scale = np.exp(np.stack([c["scale_0"], c["scale_1"], c["scale_2"]], 1).astype(float))
    col = np.clip(0.5 + C0 * np.stack([c["f_dc_0"], c["f_dc_1"], c["f_dc_2"]], 1), 0, 1).astype(float)
    op = 1 / (1 + np.exp(-c["opacity"].astype(float)))
    return dict(pos=pos, axes=axes, scale=scale, color=col, opacity=op)


def save(path, sp, inria=False):
    """Write a standard 3DGS PLY, SH degree 0 (opacity as logit, scale as log, rot as w x y z)."""
    n = len(sp["pos"])
    A = sp["axes"].copy()                                # rows = local axes in world
    neg = np.linalg.det(A) < 0
    A[neg, 2] *= -1                                      # make it a proper rotation
    Rm = A.transpose(0, 2, 1)                            # columns = axes
    tr = np.trace(Rm, axis1=1, axis2=2)
    w = np.sqrt(np.clip(1 + tr, 1e-12, None)) / 2
    x = (Rm[:, 2, 1] - Rm[:, 1, 2]) / (4 * w)
    y = (Rm[:, 0, 2] - Rm[:, 2, 0]) / (4 * w)
    z = (Rm[:, 1, 0] - Rm[:, 0, 1]) / (4 * w)
    # fall back to a robust conversion where w is tiny
    bad = w < 1e-3
    if bad.any():
        from numpy.linalg import eigh
        for i in np.nonzero(bad)[0]:
            M = Rm[i]
            K = np.array([[M[0,0]-M[1,1]-M[2,2], M[1,0]+M[0,1], M[2,0]+M[0,2], M[2,1]-M[1,2]],
                          [M[1,0]+M[0,1], M[1,1]-M[0,0]-M[2,2], M[2,1]+M[1,2], M[0,2]-M[2,0]],
                          [M[2,0]+M[0,2], M[2,1]+M[1,2], M[2,2]-M[0,0]-M[1,1], M[1,0]-M[0,1]],
                          [M[2,1]-M[1,2], M[0,2]-M[2,0], M[1,0]-M[0,1], M[0,0]+M[1,1]+M[2,2]]]) / 3
            v = eigh(K)[1][:, -1]
            x[i], y[i], z[i], w[i] = v
    col = np.clip(sp["color"], 0, 1)
    op = np.clip(sp["opacity"], 1e-4, 1 - 1e-4)
    cols = {"x": sp["pos"][:, 0], "y": sp["pos"][:, 1], "z": sp["pos"][:, 2],
            "nx": np.zeros(n), "ny": np.zeros(n), "nz": np.zeros(n),
            "f_dc_0": (col[:, 0] - 0.5) / C0, "f_dc_1": (col[:, 1] - 0.5) / C0, "f_dc_2": (col[:, 2] - 0.5) / C0}
    if inria:                                    # DynGsplat wants INRIA SH-3: 45 zero f_rest
        cols.update({f"f_rest_{i}": np.zeros(n) for i in range(45)})
    cols.update({
            "opacity": np.log(op / (1 - op)),
            "scale_0": np.log(np.maximum(sp["scale"][:, 0], 1e-7)),
            "scale_1": np.log(np.maximum(sp["scale"][:, 1], 1e-7)),
            "scale_2": np.log(np.maximum(sp["scale"][:, 2], 1e-7)),
            "rot_0": w, "rot_1": x, "rot_2": y, "rot_3": z})
    if inria:
        hidden = sp["opacity"] < 1e-3                       # padded/hidden splats: logit -20
        cols["opacity"] = np.where(hidden, -20.0, cols["opacity"])
    names = list(cols)
    head = "ply\nformat binary_little_endian 1.0\ncomment claude-wafer splat look-dev (ticket 1077)\n"
    head += f"element vertex {n}\n" + "".join(f"property float {k}\n" for k in names) + "end_header\n"
    arr = np.stack([np.asarray(cols[k], dtype="<f4") for k in names], 1)
    with open(path, "wb") as f:
        f.write(head.encode())
        f.write(arr.tobytes())
