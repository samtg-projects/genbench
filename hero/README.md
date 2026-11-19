# Hero rose v2 (task 1376)

The six-stage white rose (TripoSplat, y-down; PLYs plane file 2668, bundle `757a07b0`), re-posed at the stem.

- `measure.py ply…`: stem centreline per height band (median x, z and width).
- `align.py OUTDIR`: reads `dl/six/<id>.ply`, rotates each stage about its stem base until the stem is vertical, puts every base on (0, 0.47, 0), straightens any bend left below the head (cubic, fading out at the sepals), squeezes the early stems about the axis, and scales the bud and opening heads from their base. It writes `<stage>.ply` and `align.json` (per-stage tilt, shift and factors; the run's copy is here).
- `strip.py OUT.png ply…`: front and side views at one fixed camera, for before/after.

`plyload.py` and `splat.py` are vendored from claude-wafer's splat look-dev (numpy only). Outputs: strip file 3042, PLYs file 3043.
