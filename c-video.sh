#!/bin/bash
# Task 1357 (pathway C): image -> orbit/turntable video with Wan 2.2 TI2V-5B (mlx-video), from life25's bloom still.
set -uo pipefail
V=$HOME/var/genbench/video; O=$HOME/var/genbench/pathC; mkdir -p $O; exec >>$O/video.log 2>&1
IMG=$HOME/var/claude-wafer-1353/life25/L13.png
NEG="camera cut, zoom, morphing, flower opening, petals moving, wind, blur, text, watermark"
run() { # name prompt
  t0=$(date +%s)
  $V/venv/bin/python -m mlx_video.models.wan_2.generate --model-dir $V/Wan2.2-TI2V-5B-MLX --image $IMG \
    --prompt "$2" --negative-prompt "$NEG" --width 704 --height 704 --num-frames 121 --steps 40 --seed 42 --output-path $O/$1.mp4
  echo "$1 rc=$? gen_s=$(( $(date +%s) - t0 )) $(date -u +%FT%TZ)"
}
echo "start $(date -u +%FT%TZ)"
run orbit "Smooth 360 degree orbit shot: the camera circles slowly all the way around a single white rose on its stem. The rose is perfectly still and stays centred. Product photography, soft studio light, plain black background, sharp focus."
run turntable "Turntable product shot: a single white rose on its stem rotates slowly and steadily through a full turn about its vertical axis. The camera is locked off. The rose keeps its shape, centred, soft studio light, plain black background, sharp focus."
echo "done $(date -u +%FT%TZ)"
