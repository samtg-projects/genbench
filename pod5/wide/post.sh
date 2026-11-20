#!/bin/zsh
# Task 1384: one branch's splats from Obelisk to registered, standard-frame PLYs, a sheet and a clip (run on slice).
#   post.sh <branch> <X> <height> <holds> [register env...]      e.g. post.sh cham C 0.8 1.0 LOWS=0.25 LOWT=0.6 KEEP=0.6
set -e
b=$1; X=$2; h=$3; holds=$4; shift 4
G=${0:A:h}; W=${POD5:-/private/tmp/pod5}/$b; PY=/opt/homebrew/bin/python3
rm -rf $W && mkdir -p $W/raw $W/out && cd $W
ssh samcloud "obelisk-services -- cd ~/var/claude-producer-1384/ply-$b && tar cf - *.ply *-matte.png" 2>/dev/null | tar xf - -C raw
for f in raw/${X}[0-9][0-9].ply; do n=$(basename $f .ply); echo "raw/$n.ply $n fixed 1.0"; done > spec.txt
if [ -n "$NOALIGN" ]; then cp raw/${X}[0-9][0-9].ply out/; else $PY $G/../../hero/align.py out spec.txt > align.log; fi   # NOALIGN: no stem to fit (the iris)
env "$@" $PY $G/../register.py out/${X}00.ply $(ls out/${X}[0-9][0-9].ply | grep -v ${X}00) | tee register.log
$PY $G/front.py out/${X}00.ply raw/${X}00-matte.png $h out/${X}[0-9][0-9].ply | tee front.log
