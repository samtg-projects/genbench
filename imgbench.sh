#!/bin/bash
# Ticket 1114 image-gen benchmark on obelisk: same prompts and seeds across models, wall time per invocation.
set -u
OUT=$HOME/var/genbench/img; mkdir -p "$OUT"; cd "$OUT"
export HF_HUB_ENABLE_HF_TRANSFER=1
B=$HOME/.local/bin
P1="macro photograph of a single tight red rose bud on its stem, dew drops, soft morning light, dark green background, botanical photography"
P2="macro photograph of a red rose half open, petals unfurling, dew drops, soft morning light, dark green background, botanical photography"
P3="macro photograph of a red rose in full bloom, every petal open, dew drops, soft morning light, dark green background, botanical photography"
P4="macro photograph of a wilting red rose, petals drying, curling and browning at the edges, two fallen petals, soft light, dark green background, botanical photography"
P5="wide misty temperate rainforest in the Dandenong Ranges at dawn, tree ferns and mountain ash, volumetric light, no people"
run() { # name cmd...
  local name=$1; shift
  for i in 1 2 3 4 5; do
    eval p=\$P$i
    local t0=$(date +%s.%N 2>/dev/null || python3 -c 'import time;print(time.time())')
    t0=$(/usr/bin/python3 -c 'import time;print(time.time())')
    "$@" --prompt "$p" --seed 1 2 --width 1024 --height 1024 --output "$OUT/${name}_p${i}_seed{seed}.png" > "$OUT/${name}_p${i}.log" 2>&1
    rc=$?
    t1=$(/usr/bin/python3 -c 'import time;print(time.time())')
    echo "{\"model\":\"$name\",\"prompt\":$i,\"images\":2,\"rc\":$rc,\"wall_s\":$(/usr/bin/python3 -c "print(round($t1-$t0,1))")}" >> "$OUT/timings.jsonl"
    [ $rc -ne 0 ] && { tail -5 "$OUT/${name}_p${i}.log"; break; }
  done
}
run zimage-turbo-q8 $B/mflux-generate-z-image-turbo -q 8 --steps 9
run flux3-klein-q8 $B/mflux-generate-flux3 -m flux3-image-klein -q 8
run flux2-klein-4b-q8 $B/mflux-generate-flux2 -m flux2-klein-4b -q 8
echo done
