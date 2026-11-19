#!/bin/bash
# Task 1357: analytic turntable poses for turntable.mp4 (no COLMAP), swept over the total turn; 10k-step Brush each.
set -u
P=$HOME/var/genbench/pathC; W=$P/posesweep; mkdir -p $W && cd $W && tar xzf $P/tt-frames.tgz
for T in 30 90 180 360; do
  D=$HOME/workcloud/data/nerfstudio/pathC-pose-t$T/dataset; rm -rf $D; mkdir -p $D/images
  ln frames/f_*.png $D/images/
  /usr/bin/python3 mk_tf.py $D 121 $T 25 20
  curl -s -X POST localhost:8420/train -F dataset_path=$D -F name=pathC-pose-t$T -F max_num_iterations=10000; echo
done
