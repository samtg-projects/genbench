# Pod 5, going wide (task 1384, claude-producer)

Trent's rock (05), chameleon (08), strangler fig (02), iris (06) and his 12 standalone flowers, through claude-wafer's flow
(`../README.md`). Built from Trent's concepts and references (doc 670); credit them that way.

- **Stills** (`stills.py`, klein on Obelisk, seed 7): every anchor is a klein edit of Trent's own frame (crops of files
  3084–3093), and every stage is an edit of the anchor or the stage before, with Trent's matching frame as a second image.
  - chameleon: one pose from Trent's frame 01; the 20 skins are each an edit of that anchor, so pose and log hold.
  - iris: klein moved the pupil too little, so `iris_warp.py` makes the pupil frames by radially warping one still (the
    pattern is identical in every frame; the edge stays fixed). Frames 04 and 08 are klein's warm and cool light edits.
  - rock: klein repainted the rock from stage 4 on, so `rock_zone.py` composites only each growth zone onto the bare rock
    K00 (the rock is immutable by construction). All five zones (`stills.py zone …`): moss, lichen, sickle fern, rock
    orchid, native vine. The lichen's stages come from `lichen_grow.py` (one peak patch revealed over a growing radius,
    then aged), because klein drew it all at once; the vine's decay is aged in `rock_zone.py`.
  - fig: chained edits from a fixed soil patch; stages 5–9 are a miniature (Trent: the big canopy looked "jank" at 30k),
    stage 8 an edit from the bare soil because the remove-the-leaves edit came back unchanged.
- **Splats** (`splat.sh` → `tsplat_lum.py`): TripoSplat with mattes that keep the anchor. BiRefNet took the chameleon and
  dropped its log, so each matte is max(BiRefNet, the non-black regions touching its subject), closed to fill dark grain.
- **Frame** (on slice, `post.sh`): `../../hero/align.py` fixed mode, `../register.py` onto the anchor stage, then
  `front.py` (finds the photo front by silhouette match, standard frame: front +x, so view -1,0,0; y-down; base at
  (0, 0.47, 0)). The iris is a flat ring ICP can't hold, so `iris_norm.py` then `iris_size.py` instead.
- **Rock zones in 3D** (`zones.sh`): each zone's stages are registered onto the moss run's K00; its layer is the splats
  new over K00 (`zone_layer.py`) or, for flat or thin zones, its own colour on the rock's surface (`lichen_layer.py`,
  teal for the lichen, `COLOR=green` for the vine). `rock_all.py` stacks all five layers on K00; `zones_sheet.py` shows
  each zone close up.
- **Sheets and clips**: `sheet.py` (Trent's frame | our still | our splat front and 35°), `clip.py` (the player's
  rank-order dissolve, holds as an argument, frames across processes). `contact.py` makes plain still contact sheets.
