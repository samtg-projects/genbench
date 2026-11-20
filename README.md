# genbench

Scripts for local image, video and splat generation on Obelisk (Mac Studio, M5 Max, 128 GB), from the Phoria samcloud satellite hackathon, 19 Nov 2026. They run in the `obelisk-services` account from `~/var/genbench/`, the live copy; this repo mirrors it. What works, measurements and caveats are in samcloud [doc 660](https://cloud.samtg.xyz/docs/660); the Obelisk host setup is in [doc 658](https://cloud.samtg.xyz/docs/658).

Every GPU run is a claim on `obelisk-services/gpu-0` through `~/.local/bin/obelisk-job` (compute-jobs). Training goes through Obelisk's nerfstudio-api (`127.0.0.1:8420`, Brush 0.3.0). The `start-*.py` files are one-off launchers: each starts one detached claim with a `--purpose` naming its ticket or task, and they double as a record of what was run.

## Layout

| path | what |
|---|---|
| `imgbench.sh`, `start-bench.py`, `peaks.py` | image-model benchmark (FLUX.2 klein, Z-Image Turbo) and memory peaks |
| `video.sh`, `c-video.sh`, `c-video2.sh`, `start-c.py`, `start-c2.py` | Wan 2.2 TI2V-5B via mlx-video (exclusive claims) |
| `tsplat.sh`, `tsplat_stream.py`, `start-series.py`, `start-life25.py`, `start-life28.py`, `start-nature.py` | TripoSplat, image → 262k-Gaussian splat; streams over a folder of stages in one claim |
| `tsplat_masked.py`, `start-masked.py` | TripoSplat with our own mattes for chained-edit series: base-stage matte kept in every stage, one shared crop |
| `align_plane.py`, `align_base.py`, `extent.py` | stage alignment (PCA plane to a reference or axis; ground and base centre) and extent checks |
| `preview.py`, `align_sheet.py`, `prep_tile.py`, `grid.py`, `crop.py`, `wip.py` | sheets and process videos with nerfstudio-api's CPU point renderer |
| `synth/` | pathway B/D: Blender Cycles multicam → `transforms.json` → Brush. `render_multicam.py` (env `VIEWS RES SPP DIST ELEV SUN TRANSPARENT BG`), `scene_cloud.py`, `scene_nebula.py`, `full-scene.sh <scene.py> <name> <views> <res> <spp> [seed]` |
| `seat-tools/ob-image`, `seat-tools/ob-triposplat` | installed in `obelisk-services:~/.local/bin` for hermes-obelisk (task 1398): queue images through Obelisk's image service, and image → splat through TripoSplat, as the calling seat |
| `pathC/`, `pathC-splat.sh` | pathway C: image → Wan turntable → splat. `posesweep/mk_tf.py` (analytic circle poses), `seed.py` (seed points; Brush's random init misses the origin for an arc of cameras), `fitpose.py` (per-frame azimuth/elevation fit against a trained splat), `compare.py`, `where.py` |

## Conventions

- TripoSplat PLYs are y-down, and the input image looks along −x (`splatFrame` view `-1,0,0`).
- Synthetic and pathway C datasets are z-up, OpenGL camera-to-world (`[right, up, -forward, centre]`).
- No credentials live here. `tsplat.sh` reads plane files with the account's header file (`~/.samcloud/token.hdr`), never a token in the script.
