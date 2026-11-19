#!/bin/bash
# Task 1357: why did the analytic-pose runs collapse to 2 splats? Brush 2000 steps on t90 with its output kept.
D=$HOME/workcloud/data/nerfstudio/pathC-pose-t90/dataset; ~/projects/nerfstudio-api/.venv/bin/python $HOME/var/genbench/pathC/posesweep/seed.py $D 20000 1.0
O=$HOME/var/genbench/pathC/posesweep/diag2; rm -rf $O; mkdir -p $O
$HOME/.local/bin/obelisk-job run samclaude-1357-brushdiag2-$(date +%s) --purpose "task 1357: Brush 2000-step diagnostic on analytic poses, seeded" --memory 8192 -- \
  /bin/sh -c "$HOME/.local/bin/brush_app $D --total-steps 2000 --export-every 500 --export-path $O --export-name e_{iter}.ply > $O/brush.log 2>&1; echo rc=\$? >> $O/brush.log"
