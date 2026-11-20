# Pod 5: Trent's nature concepts through our flow (doc 670)

Built from Trent's concepts and references. Credit them that way.

**Waratah (task 1380).**
- **Stills:** FLUX.2 klein 4B q8 on Obelisk. `waratah.py` makes the 10 stages as text-to-image across seeds 7, 11, 23 and 42, plus edit chains off the full bloom. `seed.py` re-runs the seed stage without the stem framing. `chain.py` makes stages 5–10 as chained edits from the closed bud, and that is the set used. `waratah/stills_map.txt` says which still became which stage.
- **Splats:** TripoSplat via `../tsplat_stream.py` on a pick dir.
- **Alignment:** `../hero/align.py OUT waratah/spec.txt`. In the spec, `rigid` stands the base→head line upright with no bend straightening, `fixed` handles the seed, and the last column is the stage height from Trent's storyboard ratios.
- **Clip:** `clip.py OUTDIR x ply…` renders it with Trent's holds and a keyed dissolve.

**Ending (Mel's story):** `ending.py` makes dry remains → soil mound → mycelium threads (text-to-image, then chained edits).

**Stage 10 (the published set):** `dry.py` recolours the aligned 09 splat in place, so 09→10 dissolves continuously. The klein drying edit had come back unchanged.

**Ending, as published:**
- **Stills:** E01–E04 are M1, M3, M5 and M6 on seed 7. `ending2.py` adds M5 and M6 (denser mycelium).
- **Splats:** `../tsplat_masked.py`, with each stage unioned with the E03 mound.
- **Alignment:** `../hero/align.py` in fixed mode, then `mound.py 0.45` equalises the mound widths. E04 is then matched to E03's height, because its outward threads skew the width.

**Pixie parasol (task 1381):**
- **Stills:** `pixie2.py` makes the bark-chip anchor, then chained edits (P01–P09, seed 11). `pixie.py` was the first pass, with the bark too large and a spore fog. It's kept for the record.
- **Stage 10:** a copy of stage 03, because the mycelium survives.
- **Splats:** `../tsplat_masked.py`, each stage unioned with F01.
- **Alignment:** `../hero/align.py` in fixed mode, then `setrot.py v2/F06.ply 0.93 …`, one shared rotation and scale for the whole set.

**Anchor registration (pixie v3, ghost):** TripoSplat re-centres and rescales each stage by its own extent, so a fixed anchor (bark, log) drifts. `register.py REF ply…` with `LOWS=0.25 LOWT=0.6` runs a trimmed ICP (similarity transform) of each stage's lowest quarter, where only the anchor sits, onto the reference's anchor. After that come the shared `setrot.py` and a recentre on the reference.

**Ghost fungus:** `ghost.py`, then `ghost_fix.py` (Q04, Q05 and Q09 re-worded), seed 23. Stage 10 is stage 03 again.
**Butterfly:** `butterfly.py` makes a bare host-twig anchor with several short edit chains branching from it, so the twig holds its coordinates.

**register.py multi-start:** `STARTS=N` tries N random starting rotations. `SMIN` and `MAXROT` bound the scale and the rotation, and the fit with the lowest trimmed rms wins.
- **Lorikeet:** registers well on the branch, because the nest and blossom give it bulk. K04, K11, K12 and K17 needed `SMIN=0.75 MAXROT=25`.
- **Butterfly:** parked. The thin twig makes every fit collapse to the scale floor. The next try is render-and-compare against each frame's own matte.

**Reef (staghorn):** `reef.py`, seed 7, registered on the bare rock R00 (`LOWS=0.25 KEEP=0.6`). From stage 5 the rock's back changes shape, because TripoSplat re-invents it once the thicket appears.

**Quality pass (task 1383):**
- **Diagnosis:** `diag.py STAGE.ply OUT N…` renders the full count against thinned versions, from front, side and back, with a head close-up.
- **Finding:** the patchiness is the thinning. The ⅓ opacity-sampled share scatters tiny opaque splats as speckles. Importance-only thinning (opacity × projected area) is clean at the same count.
- **Tests:** `thin_test.py` and `thin2.py` compare the recipes. A head bias starves the leaves, so it was rejected.
