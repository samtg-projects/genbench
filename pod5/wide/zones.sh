#!/bin/zsh
# Task 1384, rock: one more growth zone on the same rock (run on slice once its stills exist on Obelisk).
#   zones.sh <zone> <moss-run K00.ply>    composite -> TripoSplat (Obelisk claim) -> register onto that K00 -> zone layer
set -e
z=$1; K00=$2; G=${0:A:h}; W=${POD5:-/private/tmp/pod5}/zone-$z; PY=/opt/homebrew/bin/python3; R=/Users/obelisk-services/var/claude-producer-1384
rm -rf $W && mkdir -p $W/src $W/comp $W/up/rockz-$z $W/raw $W/out $W/final
ssh samcloud "obelisk-services -- cd $R/zone-$z && tar cf - K*_seed_7.png" 2>/dev/null | tar xf - -C $W/src
$PY $G/rock_zone.py $W/src $W/comp $z | tail -1
for k in $(seq -w 0 10); do cp $W/comp/K$k.png $W/up/rockz-$z/K${k}_seed_7.png; done
(cd $W/up && tar cf - rockz-$z) | ssh samcloud "obelisk-services -- tar xf - -C $R" 2>/dev/null
ssh samcloud "obelisk-services -- ~/.local/bin/obelisk-job run cp1384-splat-$z --purpose 'task 1384: pod5 rock $z zone TripoSplat, claude-producer' --memory 16384 --cwd $R -- $R/genbench/splat.sh rockz-$z" 2>/dev/null | tail -1
until [ "$(ssh samcloud "obelisk-services -- ls $R/ply-rockz-$z 2>/dev/null | grep -c '^K[0-9][0-9].ply'" 2>/dev/null | tail -1)" -ge 11 ]; do sleep 20; done
ssh samcloud "obelisk-services -- cd $R/ply-rockz-$z && tar cf - K*.ply" 2>/dev/null | tar xf - -C $W/raw
cp $W/raw/K*.ply $W/out/
LOWS=1 LOWT=1 KEEP=0.7 $PY $G/../register.py $K00 $(ls $W/out/K[0-9][0-9].ply | grep -v K00) > $W/register.log
EPS=0.025 $PY $G/zone_layer.py $W/final $K00 $(ls $W/out/K[0-9][0-9].ply | grep -v K00) | tee $W/layer.log
cp $K00 $W/final/K00.ply
