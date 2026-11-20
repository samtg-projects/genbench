"""Task 1383 (claude-wafer): waratah v2, closer to Trent's storyboard (file 3082) and with in-betweens.
Trent's tiles T01-T10 are the reference inputs. S07 = photoreal re-render of T07; S08-S10 chain forward from S07, S06-S04 chain backward,
each edit taking [previous stage, Trent's tile for the target stage]; S01-S03 re-render T01-T03. Then halfway in-betweens Mk between
neighbours (k.5). Seeds 7, 23. Output ~/var/claude-wafer-1380/w2/."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/w2"; T = f"{B}/trent"
SEEDS = ["7", "23"]; ED = f"{H}/.local/bin/mflux-generate-flux2-edit"
LOOK = "photorealistic botanical photograph, pure black background, real textures, broad soft light, sharp detail, no text, no people"
KEEP = "Keep image 1's camera, framing, scale, stem position and pure black background exactly the same."
NAME = {1: "seed", 2: "seedling", 3: "early stem", 4: "closed bud", 5: "opening bloom", 6: "peak bloom", 7: "full bloom", 8: "wilting", 9: "decaying, dried brown, aged and lifeless, not gory", 10: "dry remains, shrivelled and brown, aged and lifeless"}
log = open(f"{B}/runs.jsonl", "a")
def edit(imgs, prompt, out, s):
    if os.path.exists(out): return
    t0 = time.time(); r = subprocess.run([ED, "-m", "flux2-klein-4b", "-q", "8", "--image-paths", *imgs, "--prompt", prompt, "--seed", s, "--output", out], capture_output=True, text=True)
    log.write(json.dumps(dict(out=os.path.basename(out), imgs=[os.path.basename(i) for i in imgs], prompt=prompt, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
    print(os.path.basename(out), r.returncode, flush=True)
for s in SEEDS:
    S = lambda k: f"{B}/S{k:02d}_seed_{s}.png"
    edit([f"{T}/T07.png"], f"Recreate this New South Wales waratah (Telopea speciosissima) at full bloom as a {LOOK}: the same pose, crimson domed flower head, spreading bracts, short stem and leathery serrated leaves, the same framing.", S(7), s)
    for k in (8, 9, 10):
        edit([S(k - 1), f"{T}/T{k:02d}.png"], f"Change the waratah in image 1 so it matches the stage shown in image 2: {NAME[k]}. {KEEP} {LOOK}.", S(k), s)
    for k in (6, 5, 4):
        edit([S(k + 1), f"{T}/T{k:02d}.png"], f"Change the waratah in image 1 so it matches the stage shown in image 2: {NAME[k]}. {KEEP} {LOOK}.", S(k), s)
    for k in (1, 2, 3):
        edit([f"{T}/T{k:02d}.png"], f"Recreate this waratah {NAME[k]} as a {LOOK}: the same subject, size in frame and framing.", S(k), s)
    for k in range(1, 10):
        edit([S(k), S(k + 1)], f"Show the waratah at the stage exactly halfway between image 1 and image 2: an in-between growth stage. {KEEP} {LOOK}.", f"{B}/M{k:02d}_seed_{s}.png", s)
print("waratah2 done", flush=True)
