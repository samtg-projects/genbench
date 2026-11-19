# Task 1361: translate each stage so its ground (98th pct of y, y-down) and base-band centre (median x, z) sit on the reference's.
#   align_base.py <in_dir> <out_dir> S01.ply S02.ply ...   (first is the reference)
import sys, numpy as np
from pathlib import Path
def read(p):
    b = open(p, "rb").read(); h = b.index(b"end_header\n") + 11; head = b[:h].decode()
    n = int(head.split("element vertex ")[1].split("\n")[0]); props = [l.split()[-1] for l in head.splitlines() if l.startswith("property float")]
    return head, np.frombuffer(b[h:], dtype=[(k, "<f4") for k in props], count=n).copy()
def base(v):
    m = v["opacity"] > 0; y = v["y"][m]; g = np.percentile(y, 98); b = y > np.percentile(y, 60)
    return np.array([np.median(v["x"][m][b]), g, np.median(v["z"][m][b])])
ind, outd = Path(sys.argv[1]), Path(sys.argv[2]); outd.mkdir(parents=True, exist_ok=True); names = sys.argv[3:]
ref = base(read(ind / names[0])[1])
for nm in names:
    head, v = read(ind / nm); d = ref - base(v)
    for k, dk in zip("xyz", d): v[k] += np.float32(dk)
    open(outd / nm, "wb").write(head.encode() + v.tobytes()); print(nm, "shift", d.round(3))
