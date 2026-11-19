#!/bin/bash
# Task 1357 (pathway C), video round 2: continue the turntable from its last frame (to extend the turn), plus a second seed.
set -uo pipefail
V=$HOME/var/genbench/video; O=$HOME/var/genbench/pathC; exec >>$O/video2.log 2>&1
FF=$HOME/.local/bin/ffmpeg
NEG="camera cut, zoom, morphing, flower opening, petals moving, wind, blur, text, watermark"
P="Turntable product shot: a single white rose on its stem rotates slowly and steadily through a full turn about its vertical axis. The camera is locked off. The rose keeps its shape, centred, soft studio light, plain black background, sharp focus."
run() { # name image seed
  t0=$(date +%s)
  $V/venv/bin/python -m mlx_video.models.wan_2.generate --model-dir $V/Wan2.2-TI2V-5B-MLX --image $2 \
    --prompt "$P" --negative-prompt "$NEG" --width 704 --height 704 --num-frames 121 --steps 40 --seed $3 --output-path $O/$1.mp4
  echo "$1 rc=$? gen_s=$(( $(date +%s) - t0 )) $(date -u +%FT%TZ)"
}
echo "start $(date -u +%FT%TZ)"
$FF -loglevel error -y -sseof -0.05 -i $O/turntable.mp4 -frames:v 1 $O/turntable-last.png
run turntable-cont $O/turntable-last.png 42
$FF -loglevel error -y -sseof -0.05 -i $O/turntable-cont.mp4 -frames:v 1 $O/turntable-cont-last.png
run turntable-cont2 $O/turntable-cont-last.png 42
run turntable-s7 $HOME/var/claude-wafer-1353/life25/L13.png 7
echo "done $(date -u +%FT%TZ)"
