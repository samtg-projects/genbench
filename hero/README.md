# Hero rose v2 (task 1376)

The six-stage white rose (TripoSplat, y-down; PLYs plane file 2668, bundle `757a07b0`), re-posed at the stem.

- `measure.py ply…`: stem centreline per height band (median x, z and width).
- `align.py OUTDIR`: reads `dl/six/<id>.ply`, rotates each stage about its stem base until the stem is vertical, puts every base on (0, 0.47, 0), straightens any bend left below the head (cubic, fading out at the sepals), squeezes the early stems about the axis, and scales the bud and opening heads from their base. It writes `<stage>.ply` and `align.json` (per-stage tilt, shift and factors; the run's copy is here).
- `strip.py OUT.png ply…`: front and side views at one fixed camera, for before/after.

`plyload.py` and `splat.py` are vendored from claude-wafer's splat look-dev (numpy only). Outputs: strip file 3042, PLYs file 3043.

## life25 v2 (task 1379)

The same alignment on the 28-stage life25 v2 (TripoSplat sources `obelisk-services:~/var/genbench/triposplat/life28/L01…L28.ply`, bundle `8badcc89`). `align.py OUTDIR life25v2/spec.txt` (paths relative to a dir holding `life28/`). The squeeze `auto:0.025` thins a stem to the bloom-stage width only where it measures over 1.15×. That applies to L01–L03 and L05–L08. The heads are untouched. `survey.py ply…` prints tilt, base and stem width per stage. Outputs: strip file 3080, PLYs file 3081.
