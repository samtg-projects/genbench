#!/bin/bash
# Ticket 1114 video smoke: mlx-video + Wan2.2 TI2V-5B (Apache-2.0), image-to-video from a FLUX.2 klein still.
set -uo pipefail
V=$HOME/var/genbench/video; mkdir -p $V; cd $V
exec >>$V/video.log 2>&1
echo "start $(date -u +%FT%TZ)"
if [ ! -x $V/venv/bin/python ]; then
  $HOME/.local/bin/uv venv -q -p 3.13 $V/venv
  $HOME/.local/bin/uv pip install -q -p $V/venv/bin/python "git+https://github.com/Blaizzy/mlx-video.git" torch "huggingface_hub[cli]" hf_transfer || exit 3
fi
$V/venv/bin/python -c "import importlib.metadata as m;print('mlx-video',m.version('mlx-video'),'mlx',m.version('mlx'))" || true
export HF_XET_HIGH_PERFORMANCE=1
[ -f $V/Wan2.2-TI2V-5B/config.json ] || $V/venv/bin/hf download Wan-AI/Wan2.2-TI2V-5B --local-dir $V/Wan2.2-TI2V-5B || exit 4
echo "downloaded $(date -u +%FT%TZ) $(du -sh $V/Wan2.2-TI2V-5B | cut -f1)"
[ -d $V/Wan2.2-TI2V-5B-MLX ] || $V/venv/bin/python -m mlx_video.models.wan_2.convert --checkpoint-dir $V/Wan2.2-TI2V-5B --output-dir $V/Wan2.2-TI2V-5B-MLX || exit 5
echo "converted $(date -u +%FT%TZ)"
IMG=$HOME/var/genbench/img/flux2-klein-4b-q8_p1_seed1_seed_1.png
t0=$(date +%s)
$V/venv/bin/python -m mlx_video.models.wan_2.generate --model-dir $V/Wan2.2-TI2V-5B-MLX --image $IMG \
  --prompt "time-lapse photography: the red rose bud slowly opens, petals unfurl into a full bloom, static camera, dark green background, macro" \
  --width 704 --height 704 --num-frames 81 --steps 40 --seed 42 --output-path $V/rose-bloom-ti2v5b.mp4
echo "rc=$? gen_s=$(( $(date +%s) - t0 )) $(date -u +%FT%TZ)"
