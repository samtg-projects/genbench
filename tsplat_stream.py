# Ticket 1114: TripoSplat each sNN.png as it lands in SRC (load the pipeline once), until N stages are done or idle too long.
import sys, os, time, json, torch
from pathlib import Path
SRC, OUT, N = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
PAT = sys.argv[4] if len(sys.argv) > 4 else "s[0-9][0-9].png"
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(Path.home() / "var/genbench/triposplat/repo")
sys.path.insert(0, ".")
from triposplat import TripoSplatPipeline
pipe = TripoSplatPipeline(ckpt_path="ckpts/diffusion_models/triposplat_fp16.safetensors",
    decoder_path="ckpts/vae/triposplat_vae_decoder_fp16.safetensors", dinov3_path="ckpts/clip_vision/dino_v3_vit_h.safetensors",
    flux2_vae_encoder_path="ckpts/vae/flux2-vae.safetensors", rmbg_path="ckpts/background_removal/birefnet.safetensors", device="mps")
log = open(OUT / "runs.jsonl", "a"); idle = time.time()
while True:
    todo = [p for p in sorted(SRC.glob(PAT)) if not (OUT / (p.stem + ".ply")).exists()]
    if not todo:
        if len(list(OUT.glob("*.ply"))) >= N or time.time() - idle > 1800: break
        time.sleep(15); continue
    p = todo[0]; time.sleep(2)            # let the writer finish the file
    t = time.time()
    g, prepared = pipe.run(str(p), num_gaussians=262144, show_progress=False)
    prepared.save(str(OUT / (p.stem + "-prepared.webp"))); g.save_ply(str(OUT / (p.stem + ".ply")))
    rec = {"stage": p.stem, "gen_s": round(time.time() - t, 1), "peak_mps_gb": round(torch.mps.driver_allocated_memory() / 2**30, 1)}
    log.write(json.dumps(rec) + "\n"); log.flush(); print(rec, flush=True); idle = time.time()
print("done", len(list(OUT.glob("*.ply"))), flush=True)
