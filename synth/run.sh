#!/bin/bash
# Ticket 1114 synthetic multicam proof: fetch a CC0 Poly Haven flower, render N views, write transforms.json.
set -euo pipefail
A=$HOME/var/genbench/synth/asset; D=$HOME/workcloud/data/nerfstudio/${DS:-synth-gazania}/dataset; rm -rf $D/images $D/transforms.json
mkdir -p $A/textures $D
cd $A
[ -f flower_gazania_2k.blend ] || curl -fsSL -o flower_gazania_2k.blend https://dl.polyhaven.org/file/ph-assets/Models/blend/2k/flower_gazania/flower_gazania_2k.blend
for t in png/2k/flower_gazania/flower_gazania_alpha_2k.png jpg/2k/flower_gazania/flower_gazania_diff_2k.jpg exr/2k/flower_gazania/flower_gazania_nor_gl_2k.exr png/2k/flower_gazania/flower_gazania_disp_2k.png exr/2k/flower_gazania/flower_gazania_rough_2k.exr; do
  f=textures/$(basename $t); [ -f $f ] || curl -fsSL -o $f https://dl.polyhaven.org/file/ph-assets/Models/$t
done
t0=$(date +%s)
KEEP=${KEEP:-flower_gazania_h_LOD0} $HOME/Applications/Blender.app/Contents/MacOS/Blender -b $A/flower_gazania_2k.blend -P $HOME/var/genbench/synth/render_multicam.py -- $D ${VIEWS:-100} ${RES:-800} ${SPP:-64} 2>&1 | grep -E "WROTE|Error|error|Traceback" || true
echo "render_s=$(( $(date +%s) - t0 ))"
ls $D/images | wc -l
