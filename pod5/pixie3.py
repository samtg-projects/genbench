"""Task 1383 step 3 (claude-wafer): pixie parasol v3 with Trent's storyboard (file 3085) tiles T01-T10 as the edit targets, plus targeted
in-betweens. S06 = photoreal re-render of T06; S07-S10 chain forward and S05-S04 backward, each edit taking [previous stage, Trent's tile];
S01-S03 re-render T01-T03. Targeted in-betweens J45, J56, J89. Seeds 7, 23. Output ~/var/claude-wafer-1380/pix3/."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/pix3"; T = f"{B}/trent"
SEEDS = ["7", "23"]; ED = f"{H}/.local/bin/mflux-generate-flux2-edit"
LOOK = "photorealistic macro nature photograph, pure black background, real textures, translucent caps, broad soft light, sharp detail, no text, no people"
KEEP = "Keep image 1's camera, framing, scale, the bark's shape and position, and the pure black background exactly the same."
NAME = {1: "spores", 2: "germinating spores", 3: "mycelium spreading over a piece of bark", 4: "primordia: three slender stalks with round blue tips",
        5: "emergence: three young mushrooms with small cyan bell caps", 6: "vibrant maturity", 7: "spore release: a faint compact haze of spores under the caps",
        8: "senescence: the caps fading paler, edges curling", 9: "decomposition: collapsed, shrivelled, translucent brown, aged and lifeless, not gory",
        10: "return to substrate: only the bark with a few shrivelled translucent fragments, aged and lifeless"}
log = open(f"{B}/runs.jsonl", "a")
def edit(imgs, prompt, out, s):
    if os.path.exists(out): return
    t0 = time.time(); r = subprocess.run([ED, "-m", "flux2-klein-4b", "-q", "8", "--image-paths", *imgs, "--prompt", prompt, "--seed", s, "--output", out], capture_output=True, text=True)
    log.write(json.dumps(dict(out=os.path.basename(out), imgs=[os.path.basename(i) for i in imgs], prompt=prompt, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
    print(os.path.basename(out), r.returncode, flush=True)
for s in SEEDS:
    S = lambda k: f"{B}/S{k:02d}_seed_{s}.png"
    edit([f"{T}/T06.png"], f"Recreate these three pixie parasol mushrooms (Mycena interrupta) on bark at vibrant maturity as a {LOOK}: the same pose, cyan-blue ribbed translucent caps, slender white stems, the same bark chip and framing.", S(6), s)
    for k in (7, 8, 9, 10):
        edit([S(k - 1), f"{T}/T{k:02d}.png"], f"Change the mushrooms in image 1 so they match the stage shown in image 2: {NAME[k]}. {KEEP} {LOOK}.", S(k), s)
    for k in (5, 4):
        edit([S(k + 1), f"{T}/T{k:02d}.png"], f"Change the mushrooms in image 1 so they match the stage shown in image 2: {NAME[k]}. {KEEP} {LOOK}.", S(k), s)
    for k in (1, 2, 3):
        edit([f"{T}/T{k:02d}.png"], f"Recreate this pixie parasol stage, {NAME[k]}, as a {LOOK}: the same subject, size in frame and framing.", S(k), s)
    for a, desc in ((4, "the three blue-tipped stalks are taller, each tip swelling into a small closed blue cap"),
                    (5, "the three cyan caps have opened halfway into wider bells"),
                    (8, "the pale caps are starting to collapse and droop, stems bending, turning translucent brown at the edges")):
        edit([S(a)], f"The same scene; {desc}. {KEEP} {LOOK}.", f"{B}/J{a}{a+1}_seed_{s}.png", s)
print("pixie3 done", flush=True)
