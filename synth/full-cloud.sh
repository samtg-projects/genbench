#!/bin/bash
# Pathway D scene proof (doc 661): procedural cumulus volume -> 160-view transparent multicam render (claimed) -> Brush via nerfstudio-api.
set -u
S=$HOME/var/genbench/synth; L=$S/full-cloud.log; exec >>"$L" 2>&1
DS=synth-cloud-v1; D=$HOME/workcloud/data/nerfstudio/$DS/dataset; B=$HOME/Applications/Blender.app/Contents/MacOS/Blender
echo "start $(date -u +%FT%TZ)"
$B -b --factory-startup -P $S/scene_cloud.py -- $S/cloud.blend | grep -E "SAVED|Error"
rm -rf $D; mkdir -p $D
K=samclaude-pathD-cloud-render-$(date +%s)
$HOME/.local/bin/obelisk-job run $K --purpose "pathway D (doc 661): procedural cloud, 160 views 1024px 64spp transparent" --memory 16384 -- \
  /bin/sh -c "t0=\$(date +%s); KEEP=cloud TRANSPARENT=1 DIST=0.6 $B -b $S/cloud.blend -P $S/render_multicam.py -- $D 160 1024 64 2>&1 | grep -E 'WROTE|Error|Traceback'; echo render_s=\$(( \$(date +%s) - t0 ))"
while :; do s=$($HOME/.local/bin/obelisk-job status $K 2>/dev/null | /usr/bin/python3 -c "import json,sys;d=json.load(sys.stdin);print('done' if d.get('release') else 'wait')" 2>/dev/null); [ "$s" = done ] && break; sleep 20; done
cat $HOME/.local/state/samcloud/compute-jobs/$K/exec/out.log
echo "render done $(date -u +%FT%TZ) images=$(ls $D/images | wc -l)"
curl -s -X POST localhost:8420/train -F dataset_path=$D -F name=$DS-160v -F max_num_iterations=30000
echo; echo "train submitted $(date -u +%FT%TZ)"
