"""Task 1384: put a registered set in the standard frame (front +x, so registry view -1,0,0; y-down; base at (0, 0.47, 0)).
TripoSplat sometimes turns a subject about the vertical (the chameleon came out about 40 degrees off), so the photo front
is found by rendering REF's silhouette from the side over a sweep of azimuths and matching it to REF's own still matte.
    front.py REF.ply MATTE.png HEIGHT ply...      (in place; REF is usually the anchor; HEIGHT is REF's height after)
    AZ=deg skips the search."""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload, splat
ref, matte, height, ps = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4:]
def norm_mask(m, S=128):
    ys, xs = np.nonzero(m > 127); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = m.shape; k = S / max(h, w); m = cv2.resize(m, (max(1, int(w * k)), max(1, int(h * k))))
    o = np.zeros((S, S), np.uint8); o[(S - m.shape[0]) // 2:(S - m.shape[0]) // 2 + m.shape[0], (S - m.shape[1]) // 2:(S - m.shape[1]) // 2 + m.shape[1]] = m; return o > 127
want = None if "AZ" in os.environ else norm_mask(cv2.imread(matte, cv2.IMREAD_UNCHANGED)[:, :, 3])
sp = plyload.load(ref); o = sp["opacity"] > 0.3; ctr = np.median(sp["pos"][o], 0); rad = np.percentile(np.linalg.norm(sp["pos"][o] - ctr, axis=1), 98)
sub = {k: v[o][::max(1, o.sum() // 40000)] for k, v in sp.items()}
def sil(az):
    a = np.radians(az); d = np.array([np.cos(a), 0, np.sin(a)])
    R, t = splat.look_at(ctr + d * rad * 3, ctr, up=(0, -1, 0))
    s2 = dict(sub); s2["color"] = np.ones_like(sub["color"])
    img, _ = splat.render(s2, R, t, 256 * 0.9, 256, 256, (0, 0, 0)); return (img[:, :, 0] * 255).astype(np.uint8)
best = None
if "AZ" in os.environ: best = (1.0, float(os.environ["AZ"]), 0)
else:
    for az in range(-90, 91, 5):
        for flip in (0, 1):
            m = norm_mask(sil(az)); m = m[:, ::-1] if flip else m
            iou = (m & want).sum() / max(1, (m | want).sum())
            if best is None or iou > best[0]: best = (iou, az, flip)
iou, az, flip = best; print("front at azimuth", az, "mirror" if flip else "", "iou", round(float(iou), 3))
# turn every stage about the vertical through REF's centre so the camera direction (cos az, 0, sin az) becomes +x
a = -np.radians(az); R = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
def apply(sp, M):
    A = sp["axes"] * sp["scale"][:, :, None]; S = np.einsum("nki,nkj->nij", A, A); S = M @ S @ M.T
    w, V = np.linalg.eigh(S); sp["scale"] = np.sqrt(np.clip(w, 1e-14, None)); sp["axes"] = np.swapaxes(V, 1, 2)
sps = [plyload.load(p) for p in ps]
for x in sps: x["pos"] = (x["pos"] - ctr) @ R.T + ctr; apply(x, R)
r = sps[ps.index(ref)] if ref in ps else None
P = (r if r is not None else sp)["pos"]; oo = (r if r is not None else sp)["opacity"] > 0.5
if r is None: P = (P - ctr) @ R.T + ctr
base = np.array([np.median(P[oo, 0]), np.percentile(P[oo, 1], 99.5), np.median(P[oo, 2])]); top = np.percentile(P[oo, 1], 0.5)
g = height / (base[1] - top); piv = np.array([0, 0.47, 0])
for p, x in zip(ps, sps): x["pos"] = piv + (x["pos"] - base) * g; x["scale"] *= g; plyload.save(p, x)
print("scale", round(float(g), 3), "base", np.round(base, 3))
