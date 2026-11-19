#!/bin/bash
# Ticket 1114: full synthetic proof. Render under its own claim, then train through Obelisk's nerfstudio-api (which claims itself).
set -u
L=$HOME/var/genbench/synth/full-v2.log; exec >>"$L" 2>&1
echo "start $(date -u +%FT%TZ)"
K=samclaude-1114-synth-render-$(date +%s)
$HOME/.local/bin/obelisk-job run $K --purpose "ticket 1114: synthetic multicam render, Gazania h v2: transparent, closer, 160 views 1024px 128spp" --memory 12288 -- env DS=synth-gazania-v2 TRANSPARENT=1 DIST=0.55 VIEWS=160 RES=1024 SPP=128 $HOME/var/genbench/synth/run.sh
# run returns once the work has begun; wait for its release.
while :; do s=$($HOME/.local/bin/obelisk-job status $K | /usr/bin/python3 -c "import json,sys;d=json.load(sys.stdin);print('done' if d.get('release') else 'wait')"); [ "$s" = done ] && break; sleep 15; done
cat $HOME/.local/state/samcloud/compute-jobs/$K/exec/out.log
echo "render done $(date -u +%FT%TZ)"
curl -s -X POST localhost:8420/train -F dataset_path=$HOME/workcloud/data/nerfstudio/synth-gazania-v2/dataset -F name=synth-gazania-v2-160v -F max_num_iterations=30000
echo; echo "train submitted $(date -u +%FT%TZ)"
