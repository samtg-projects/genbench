#!/bin/bash
# Ticket 1114: single image -> 3D Gaussians with the official TripoSplat (MIT) on PyTorch MPS.
set -uo pipefail
T=$HOME/var/genbench/triposplat; mkdir -p $T; cd $T
exec >>$T/run.log 2>&1
echo "start $(date -u +%FT%TZ)"
[ -d repo ] || git clone -q https://github.com/VAST-AI-Research/TripoSplat repo || exit 2
if [ ! -x venv/bin/python ]; then
  $HOME/.local/bin/uv venv -q -p 3.13 venv && $HOME/.local/bin/uv pip install -q -p venv/bin/python torch torchvision numpy safetensors pillow tqdm "huggingface_hub[cli]" || exit 3
fi
[ -f repo/ckpts/diffusion_models/triposplat_fp16.safetensors ] || venv/bin/hf download VAST-AI/TripoSplat --local-dir repo/ckpts || exit 4
echo "ready $(date -u +%FT%TZ) $(git -C repo rev-parse --short HEAD) $(du -sh repo/ckpts | cut -f1)"
mkdir -p in out
for id in "$@"; do [ -f in/$id.png ] || curl -sf -H @$HOME/.samcloud/token.hdr -o in/$id.png https://cloud.samtg.xyz/api/v1/files/$id/raw; done
cd repo
../venv/bin/python - "$@" <<'PY'
import sys, time, torch
from triposplat import TripoSplatPipeline
dev = "mps" if torch.backends.mps.is_available() else "cpu"
print("device", dev, "torch", torch.__version__, flush=True)
t = time.time()
pipe = TripoSplatPipeline(ckpt_path="ckpts/diffusion_models/triposplat_fp16.safetensors",
    decoder_path="ckpts/vae/triposplat_vae_decoder_fp16.safetensors", dinov3_path="ckpts/clip_vision/dino_v3_vit_h.safetensors",
    flux2_vae_encoder_path="ckpts/vae/flux2-vae.safetensors", rmbg_path="ckpts/background_removal/birefnet.safetensors", device=dev)
print("load_s", round(time.time() - t, 1), flush=True)
for fid in sys.argv[1:]:
    t = time.time()
    g, prepared = pipe.run(f"../in/{fid}.png", num_gaussians=262144, show_progress=False)
    prepared.save(f"../out/{fid}-prepared.webp"); g.save_ply(f"../out/{fid}.ply")
    print("file", fid, "gen_s", round(time.time() - t, 1), "peak_mps_gb", round(torch.mps.driver_allocated_memory() / 2**30, 1) if dev == "mps" else None, flush=True)
PY
echo "rc=$? $(date -u +%FT%TZ)"
