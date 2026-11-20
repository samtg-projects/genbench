"""Task 1384, rock: the zone as its own layer, and the rock immutable in 3D. After registration onto the bare rock K00,
a stage's growth is its splats that sit off K00's surface (nearest K00 splat further than EPS) inside the zone's box (the
union of off-surface splats over the peak stages, padded). Each published stage is K00, untouched, plus that layer.
    zone_layer.py OUTDIR K00.ply KNN.ply ...   writes OUTDIR/KNN.ply (rock + layer) and OUTDIR/zone/KNN.ply (layer only)"""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload
out, ref, ps = sys.argv[1], sys.argv[2], sys.argv[3:]; EPS = float(os.environ.get("EPS", 0.012))
os.makedirs(f"{out}/zone", exist_ok=True)
R = plyload.load(ref); idx = cv2.flann_Index(R["pos"].astype(np.float32), dict(algorithm=1, trees=4))
def off(sp):
    _, d = idx.knnSearch(sp["pos"].astype(np.float32), 1, params={}); return (np.sqrt(d[:, 0]) > EPS) & (sp["opacity"] > 0.05)
S = {p: plyload.load(p) for p in ps}; O = {p: off(S[p]) for p in ps}
# the zone: the densest cluster of off-surface splats at the peak stages (the cushion), grown over a voxel grid
peak = np.concatenate([S[p]["pos"][O[p]] for p in ps[len(ps) // 3: 2 * len(ps) // 3 + 1]])
V = float(os.environ.get("VOX", 0.04)); key = np.floor(peak / V).astype(int); u, cnt = np.unique(key, axis=0, return_counts=True)
dense = {tuple(k) for k, c in zip(u, cnt) if c >= np.percentile(cnt, 90)}; seed = tuple(u[np.argmax(cnt)]); zone, todo = {seed}, [seed]
while todo:
    x, y, z = todo.pop()
    for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
        nb = (x + d[0], y + d[1], z + d[2])
        if nb in dense and nb not in zone: zone.add(nb); todo.append(nb)
Z = np.array(sorted(zone)); lo, hi = Z.min(0) * V - V, (Z.max(0) + 1) * V + V
print("zone box", np.round(lo, 3), np.round(hi, 3))
for p in ps:
    sp, o = S[p], O[p]; o &= np.all((sp["pos"] >= lo) & (sp["pos"] <= hi), axis=1)
    layer = {k: v[o] for k, v in sp.items()}; both = {k: np.concatenate([R[k], layer[k]]) for k in R}
    n = os.path.basename(p); plyload.save(f"{out}/zone/{n}", layer); plyload.save(f"{out}/{n}", both)
    print(n, "layer splats", int(o.sum()))
