#!/bin/sh
# Task 1384: TripoSplat one branch's picked stills with anchor-preserving mattes (../../tsplat_masked.py): every stage's matte
# is unioned with the anchor's, and all share one crop, so the anchor (log, rock, soil, iris disc) keeps its scale.
#   splat.sh <branch> [seed]     reads ~/var/claude-producer-1384/<branch>/<X>NN_seed_<seed>.png, writes pick-<branch>/ and ply-<branch>/
set -e
R=$HOME/var/claude-producer-1384; b=$1; s=${2:-7}; PY=$HOME/var/genbench/triposplat/venv/bin/python
case $b in cham) X=C;; iris|irisw) X=I;; rock|rockc|rockz-*) X=K;; fig|figp|figp2) X=G;; flowers) X=W;; esac
mkdir -p $R/pick-$b
for f in $R/$b/${X}[0-9][0-9]_seed_$s.png; do n=$(basename $f _seed_$s.png); cp $f $R/pick-$b/$n.png; done
cd $R/pick-$b
if [ $b = flowers ]; then
  exec $PY $HOME/var/genbench/tsplat_stream.py $R/pick-$b $R/ply-$b $(ls | wc -l) "W[0-9][0-9].png"
fi
names=$(ls ${X}[0-9][0-9].png | tr '\n' ' '); union=$(ls ${X}[0-9][0-9].png | grep -v ${X}00 | sed 's/.png//' | tr '\n' ',' | sed 's/,$//')
exec $PY $HOME/var/claude-producer-1384/genbench/tsplat_lum.py $R/pick-$b $R/ply-$b ${X}00.png $union $names
