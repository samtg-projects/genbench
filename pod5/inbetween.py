"""Task 1383 step 4: halfway in-betweens for existing chained sets. For each (dir, seed, ordered keys, skip-pairs) write
dir/I_<a>_<b>_seed_S.png = klein edit of [a, b] "halfway between image 1 and image 2". Pairs listed in skip are not bridged
(a chain restart, where a halfway frame means nothing)."""
import json, os, subprocess, time
H = os.path.expanduser("~"); V = f"{H}/var/claude-wafer-1380"; ED = f"{H}/.local/bin/mflux-generate-flux2-edit"
KEEP = "Keep image 1's camera, framing, scale, the anchor's shape and position, and the pure black background exactly the same."
SETS = [
    ("pixie2", "11", "P01 P02 P03 P04 P05 P06 P07 P08 P09".split(), set(), "the pixie parasol mushrooms on the bark"),
    ("ghost", "23", "P01 P02 P03 Q04 Q05 P06 P07 P08 Q09".split(), set(), "the ghost fungus on the log"),
    ("lorikeet", "23", [f"L{i:02d}" for i in range(1, 18)], {("L07", "L08"), ("L12", "L13"), ("L16", "L17")}, "the rainbow lorikeet scene on the branch"),
]
for d, s, keys, skip, subj in SETS:
    B = f"{V}/{d}"; log = open(f"{B}/runs.jsonl", "a")
    for a, b in zip(keys, keys[1:]):
        if (a, b) in skip: continue
        out = f"{B}/I_{a}_{b}_seed_{s}.png"
        if os.path.exists(out): continue
        p = f"Show {subj} at the moment exactly halfway between image 1 and image 2: an in-between stage. {KEEP} Photorealistic, real textures."
        t0 = time.time(); r = subprocess.run([ED, "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/{a}_seed_{s}.png", f"{B}/{b}_seed_{s}.png",
                                              "--prompt", p, "--seed", s, "--output", out], capture_output=True, text=True)
        log.write(json.dumps(dict(key=os.path.basename(out), prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
        print(os.path.basename(out), r.returncode, flush=True)
print("inbetween done", flush=True)
