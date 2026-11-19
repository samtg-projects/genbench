#!/bin/bash
# Task 1357: the pose sweep again, now seeded (20k points in a unit ball, init.ply via ply_file_path); 10k-step Brush each.
set -u
W=$HOME/var/genbench/pathC/posesweep; PY=$HOME/projects/nerfstudio-api/.venv/bin/python
for T in 30 90 180 360; do
  D=$HOME/workcloud/data/nerfstudio/pathC-pose-t$T/dataset
  $PY $W/seed.py $D 20000 1.0
  curl -s -X POST localhost:8420/train -F dataset_path=$D -F name=pathC-pose-seed-t$T -F max_num_iterations=10000; echo
done
