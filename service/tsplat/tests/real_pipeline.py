"""Real-model check (run under a GPU claim where TripoSplat is installed): splat_one with fallback + both renders."""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tsplat_service import worker, render
repo = Path(sys.argv[1]).expanduser(); out = Path(sys.argv[2]).expanduser(); out.mkdir(parents=True, exist_ok=True)
w = worker.Warm({"triposplat_repo": str(repo)}, None)
w.me = type("M", (), {"lease_acquire": lambda s: "external-claim", "lease_renew": lambda s, l: None, "lease_release": lambda s, l: None})()
w.cfg["renewal_interval"] = 3600
t = time.time(); pipe = w.ensure(); print("load_s", round(time.time() - t, 1), flush=True)
for src, matte in [(a.split(":")[0], a.split(":")[1]) for a in sys.argv[3:]]:
    t = time.time(); g, prep, used = worker.splat_one(pipe, Path(src), matte, 262144, out)
    ply = out / (Path(src).stem + f"-{matte}.ply"); g.save_ply(str(ply)); prep.save(str(out / (ply.stem + "-prepared.webp")))
    s = round(time.time() - t, 1); t = time.time(); b, sh = render.beauty(ply, out), render.sheet(ply, out)
    print(json.dumps({"src": Path(src).name, "matte": matte, "used": used, "splat_s": s, "render_s": round(time.time() - t, 1), "ply_bytes": ply.stat().st_size}), flush=True)
w.release(); print("released", worker.STATE, flush=True)
