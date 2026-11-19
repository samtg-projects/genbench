#!/bin/bash
# Pathway D (doc 661): procedural scene -> transparent multicam render (claimed) -> Brush via nerfstudio-api.
# full-scene.sh <scene.py> <dataset-name> <views> <res> <spp> [seed]; env DIST, ELEV, SUN pass to render_multicam.py
set -u
SC=$1; DS=$2; V=$3; R=$4; SPP=$5; SEED=${6:-0}
S=$HOME/var/genbench/synth; L=$S/$DS.log; exec >>"$L" 2>&1
D=$HOME/workcloud/data/nerfstudio/$DS/dataset; B=$HOME/Applications/Blender.app/Contents/MacOS/Blender
OBJ=$(basename $SC .py | sed 's/^scene_//')
echo "start $(date -u +%FT%TZ)"
$B -b --factory-startup -P $S/$SC -- $S/$DS.blend $SEED | grep -E "SAVED|Error"
rm -rf $D; mkdir -p $D
K=samclaude-pathD-$DS-$(date +%s)
$HOME/.local/bin/obelisk-job run $K --purpose "pathway D (doc 661): $DS, $V views ${R}px ${SPP}spp" --memory 16384 -- \
  /bin/sh -c "t0=\$(date +%s); KEEP=$OBJ TRANSPARENT=${TRANSPARENT:-1} BG=${BG:-0.18} DIST=${DIST:-0.6} ELEV=${ELEV:--15,75} SUN=${SUN:-3.0} $B -b $S/$DS.blend -P $S/render_multicam.py -- $D $V $R $SPP 2>&1 | grep -E 'WROTE|Error|Traceback'; echo render_s=\$(( \$(date +%s) - t0 ))"
while :; do s=$($HOME/.local/bin/obelisk-job status $K 2>/dev/null | /usr/bin/python3 -c "import json,sys;d=json.load(sys.stdin);print('done' if d.get('release') else 'wait')" 2>/dev/null); [ "$s" = done ] && break; sleep 20; done
cat $HOME/.local/state/samcloud/compute-jobs/$K/exec/out.log
echo "render done $(date -u +%FT%TZ) images=$(ls $D/images | wc -l)"
curl -s -X POST localhost:8420/train -F dataset_path=$D -F name=$DS-${V}v -F max_num_iterations=30000
echo; echo "train submitted $(date -u +%FT%TZ)"
