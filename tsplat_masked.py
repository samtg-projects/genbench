# Task 1361: TripoSplat a chained-edit series with our own mattes, so each stage keeps the shared base and the same crop.
# BiRefNet alone took the mushrooms as the subject on S02-S07 and dropped the mound. Here each listed stage's matte is
# max(own matte, base stage's matte); every stage gets one shared crop (TripoSplat crops to the alpha bbox), pinned by
# two 5x5 alpha=2/255 blocks at the union bbox's corners, which composite to black.
#   tsplat_masked.py <src> <out> <base> <union stages comma-sep> SNN.png ...
import sys, os, time, json, torch, numpy as np
from pathlib import Path
from PIL import Image
SRC, OUT, BASE, UNION = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], set(sys.argv[4].split(",")); names = sys.argv[5:]
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(Path.home() / "var/genbench/triposplat/repo"); sys.path.insert(0, ".")
from triposplat import TripoSplatPipeline
pipe = TripoSplatPipeline(ckpt_path="ckpts/diffusion_models/triposplat_fp16.safetensors",
    decoder_path="ckpts/vae/triposplat_vae_decoder_fp16.safetensors", dinov3_path="ckpts/clip_vision/dino_v3_vit_h.safetensors",
    flux2_vae_encoder_path="ckpts/vae/flux2-vae.safetensors", rmbg_path="ckpts/background_removal/birefnet.safetensors", device="mps")
img = {n: Image.open(SRC / n).convert("RGB") for n in names}
mat = {}
for n in names:
    a = np.array(pipe.rmbg.remove_background(img[n]).getchannel(3)); a[a < 16] = 0; mat[n] = a
alpha = {n: np.maximum(mat[n], mat[BASE]) if Path(n).stem in UNION else mat[n] for n in names}
ys, xs = np.nonzero(np.maximum.reduce(list(alpha.values()))); H, W = alpha[names[0]].shape
x0, y0, x1, y1 = max(xs.min() - 4, 0), max(ys.min() - 4, 0), min(xs.max() + 4, W - 5), min(ys.max() + 4, H - 5)
log = open(OUT / "runs.jsonl", "a"); print("union bbox", (x0, y0, x1, y1), flush=True)
for n in names:
    a = alpha[n].copy()
    for (x, y) in ((x0, y0), (x1, y1)): a[y:y + 5, x:x + 5] = np.maximum(a[y:y + 5, x:x + 5], 2)
    rgba = img[n].copy(); rgba.putalpha(Image.fromarray(a)); rgba.save(OUT / (Path(n).stem + "-matte.png"))
    t = time.time(); g, prepared = pipe.run(rgba, num_gaussians=262144, show_progress=False)
    prepared.save(str(OUT / (Path(n).stem + "-prepared.webp"))); g.save_ply(str(OUT / (Path(n).stem + ".ply")))
    rec = {"stage": Path(n).stem, "union": Path(n).stem in UNION, "gen_s": round(time.time() - t, 1), "bbox": [int(v) for v in (x0, y0, x1, y1)]}
    log.write(json.dumps(rec) + "\n"); log.flush(); print(rec, flush=True)
print("done", flush=True)
