# Pod 5: Trent's nature concepts through our flow (doc 670)

Built from Trent's concepts and references. Credit them that way.

**Waratah (task 1380).**
- **Stills:** FLUX.2 klein 4B q8 on Obelisk. `waratah.py` makes the 10 stages as text-to-image across seeds 7, 11, 23 and 42, plus edit chains off the full bloom. `seed.py` re-runs the seed stage without the stem framing. `chain.py` makes stages 5–10 as chained edits from the closed bud, and that is the set used. `waratah/stills_map.txt` says which still became which stage.
- **Splats:** TripoSplat via `../tsplat_stream.py` on a pick dir.
- **Alignment:** `../hero/align.py OUT waratah/spec.txt`. In the spec, `rigid` stands the base→head line upright with no bend straightening, `fixed` handles the seed, and the last column is the stage height from Trent's storyboard ratios.
- **Clip:** `clip.py OUTDIR x ply…` renders it with Trent's holds and a keyed dissolve.

**Ending (Mel's story):** `ending.py` makes dry remains → soil mound → mycelium threads (text-to-image, then chained edits).
