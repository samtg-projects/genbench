"""Task 1384, rock: the whole rock, all five zones at once (Trent's 3089 shows all five layers on one rock). Stage k is the
bare rock K00 plus every zone's layer k, so the rock stays immutable and the zones grow and decay together.
    rock_all.py OUTDIR K00.ply ZONEDIR...      (each ZONEDIR holds zone/K01..K10.ply)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hero"))
import plyload
out, k00, zones = sys.argv[1], sys.argv[2], sys.argv[3:]; os.makedirs(out, exist_ok=True)
R = plyload.load(k00)
for k in range(1, 11):
    parts = [R] + [plyload.load(f"{z}/zone/K{k:02d}.ply") for z in zones]
    both = {key: np.concatenate([p[key] for p in parts]) for key in R}
    plyload.save(f"{out}/K{k:02d}.ply", both); print(f"K{k:02d}", len(both["opacity"]), "splats")
