"""Scale a set of aligned PLYs by one factor about the shared base (0, 0.47, 0) so the first reaches HEIGHT. Usage: uscale.py HEIGHT ply..."""
import sys, numpy as np
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload
h, ps = float(sys.argv[1]), sys.argv[2:]
sp0 = plyload.load(ps[0]); o = sp0["opacity"] > 0.5; g = h / (0.47 - np.percentile(sp0["pos"][o, 1], 0.5))
for p in ps:
    sp = plyload.load(p); piv = np.array([0, 0.47, 0]); sp["pos"] = piv + (sp["pos"] - piv) * g; sp["scale"] *= g; plyload.save(p, sp)
print("factor", round(g, 4))
