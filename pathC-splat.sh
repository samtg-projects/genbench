#!/bin/bash
# Task 1357: turntable clip -> nerfstudio-api dataset (every frame) -> COLMAP -> Brush 30k.
set -u; O=$HOME/var/genbench/pathC; A=http://127.0.0.1:8420; NAME=${1:-pathC-turntable}; VID=${2:-$O/turntable.mp4}; FPS=${3:-24}
L=$O/$NAME.log; log() { echo "$(date -u +%FT%TZ) $*" >> $L; }
DS=$(curl -sf -X POST $A/datasets -F name=$NAME -F source_type=video | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])') || { log FAIL dataset; exit 1; }
log dataset $DS
curl -sf -X POST $A/datasets/$DS/upload -F video=@$VID -F fps=$FPS > /dev/null || { log FAIL upload; exit 1; }
log preprocess $(curl -s -o /dev/null -w '%{http_code}' -X POST $A/datasets/$DS/preprocess)
while :; do p=$(curl -s $A/datasets/$DS/preprocess/status | python3 -c 'import json,sys;d=json.load(sys.stdin);print(int(d["preprocessing"]),int(d["has_transforms"]))'); [ "${p% *}" = 0 ] && break; sleep 15; done
D=$HOME/workcloud/data/nerfstudio/$DS/dataset
log colmap-done has_transforms=${p#* } images=$(ls $D/images 2>/dev/null | wc -l) registered=$(python3 -c "import json;print(len(json.load(open('$D/transforms.json'))['frames']))" 2>/dev/null)
[ "${p#* }" = 1 ] || { log FAIL no-transforms; exit 1; }
J=$(curl -sf -X POST $A/datasets/$DS/train -F method=splatfacto -F max_num_iterations=30000 | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])') || { log FAIL train-start; exit 1; }
log train $J
while :; do st=$(curl -s $A/jobs/$J | python3 -c 'import json,sys;print(json.load(sys.stdin)["status"])' 2>/dev/null); case "$st" in completed|failed|cancelled) break;; esac; sleep 30; done
curl -s $A/jobs/$J > $O/$NAME.json; log train-$st
