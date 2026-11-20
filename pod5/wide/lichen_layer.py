"""Task 1384, rock: the lichen layer. Lichen is a change of colour on the rock's surface, not new geometry, so the
off-surface test of zone_layer.py can't find it. Here a stage's lichen is its splats in the lichen's own teal colour, on the
rock's surface (near a bare-rock K00 splat), inside the zone's box (the densest cluster of such splats at the peak stages),
nudged PUSH outward from the rock's centre so they sit on top of K00's surface. Each stage is K00 plus that layer.
    lichen_layer.py OUTDIR K00.ply KNN.ply ...  writes OUTDIR/KNN.ply and OUTDIR/zone/KNN.ply"""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload
out, ref, ps = sys.argv[1], sys.argv[2], sys.argv[3:]; DC, PUSH = float(os.environ.get("DC", 0.14)), float(os.environ.get("PUSH", 0.004))
os.makedirs(f"{out}/zone", exist_ok=True)
R = plyload.load(ref); idx = cv2.flann_Index(R["pos"].astype(np.float32), dict(algorithm=1, trees=4))
ctr = np.median(R["pos"][R["opacity"] > 0.3], 0)
def changed(sp):
    """The lichen's own colour: klein's rosettes are teal (green and blue over red), where the rock is ochre (red over
    green over blue). Colour change against K00 alone was swamped by TripoSplat recolouring the rock between runs."""
    c = sp["color"]; _, d = idx.knnSearch(sp["pos"].astype(np.float32), 1, params={})
    if os.environ.get("COLOR") == "green":                            # the vine's leaves (and the same test serves any green zone)
        teal = (c[:, 1] > c[:, 0] + DC * 0.35) & (c[:, 1] > c[:, 2])
    else:
        teal = (c[:, 2] > c[:, 0] + DC * 0.4) & (c[:, 1] > c[:, 0])
    return teal & (np.sqrt(d[:, 0]) < 0.03) & (sp["opacity"] > 0.05)
S = {p: plyload.load(p) for p in ps}; C = {p: changed(S[p]) for p in ps}
peak = np.concatenate([S[p]["pos"][C[p]] for p in ps[4:7]])
V = 0.04; key = np.floor(peak / V).astype(int); u, cnt = np.unique(key, axis=0, return_counts=True)
dense = {tuple(k) for k, c in zip(u, cnt) if c >= np.percentile(cnt, 90)}; seed = tuple(u[np.argmax(cnt)]); zone, todo = {seed}, [seed]
while todo:
    x, y, z = todo.pop()
    for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
        nb = (x + d[0], y + d[1], z + d[2])
        if nb in dense and nb not in zone: zone.add(nb); todo.append(nb)
Z = np.array(sorted(zone)); lo, hi = Z.min(0) * V - V, (Z.max(0) + 1) * V + V; print("zone box", np.round(lo, 3), np.round(hi, 3))
for p in ps:
    sp, m = S[p], C[p] & (np.all((S[p]["pos"] >= lo) & (S[p]["pos"] <= hi), axis=1) | (os.environ.get("NOBOX") == "1"))
    layer = {k: v[m].copy() for k, v in sp.items()}; n = layer["pos"] - ctr
    layer["pos"] = layer["pos"] + PUSH * n / np.linalg.norm(n, axis=1, keepdims=True)
    both = {k: np.concatenate([R[k], layer[k]]) for k in R}; b = os.path.basename(p)
    plyload.save(f"{out}/zone/{b}", layer); plyload.save(f"{out}/{b}", both); print(b, "layer splats", int(m.sum()))
