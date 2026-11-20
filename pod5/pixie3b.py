"""Task 1383: pixie v3 fixes (seed 7). Early stages re-rendered without the word 'parasol' (klein drew umbrellas); spore release as a
light edit of S06; decay chained from S06, not from the hazy S07. Output ~/var/claude-wafer-1380/pix3/{S01b,S02b,S03b,S07b,S08b,S09b,S10b,J89b}_seed_7.png"""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/pix3"; T = f"{B}/trent"; s = "7"; ED = f"{H}/.local/bin/mflux-generate-flux2-edit"
LOOK = "photorealistic macro nature photograph, pure black background, real textures, broad soft light, sharp detail, no text, no people"
KEEP = "Keep image 1's camera, framing, scale, the bark's shape and position, and the pure black background exactly the same."
log = open(f"{B}/runs.jsonl", "a")
def edit(imgs, prompt, out):
    out = f"{B}/{out}_seed_{s}.png"
    if os.path.exists(out): return
    t0 = time.time(); r = subprocess.run([ED, "-m", "flux2-klein-4b", "-q", "8", "--image-paths", *imgs, "--prompt", prompt, "--seed", s, "--output", out], capture_output=True, text=True)
    log.write(json.dumps(dict(out=os.path.basename(out), prompt=prompt, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
    print(os.path.basename(out), r.returncode, flush=True)
S = lambda k: f"{B}/{k}_seed_{s}.png"
edit([f"{T}/T01.png"], f"Recreate this as a {LOOK}: a tiny cluster of pale translucent blue fungal spore grains, small in the lower centre of the frame. No mushrooms, no umbrella.", "S01b")
edit([f"{T}/T02.png"], f"Recreate this as a {LOOK}: a tiny cluster of pale blue fungal spores on a small crumb of bark, sprouting fine white curling hyphae threads. No mushrooms, no umbrella.", "S02b")
edit([f"{T}/T03.png"], f"Recreate this as a {LOOK}: a flat piece of brown rotting bark with bright white branching fungal mycelium spreading across its top like frost. No mushrooms, no umbrella.", "S03b")
edit([S("S06")], f"The same scene; a few tiny pale spore specks are falling just beneath each cap; nothing else changes. {KEEP} {LOOK}.", "S07b")
edit([S("S06"), f"{T}/T08.png"], f"Change the mushrooms in image 1 so they match the stage shown in image 2: senescence, the caps fading paler and their edges curling. No haze. {KEEP} {LOOK}.", "S08b")
edit([S("S08b")], f"The same scene; the pale caps are starting to collapse and droop, the stems bending, turning translucent brown at the edges. No haze. {KEEP} {LOOK}.", "J89b")
edit([S("J89b"), f"{T}/T09.png"], f"Change the mushrooms in image 1 so they match the stage shown in image 2: decomposition, collapsed and shrivelled translucent brown caps on bent stems, aged and lifeless, not gory. No haze. {KEEP} {LOOK}.", "S09b")
edit([S("S09b"), f"{T}/T10.png"], f"Change image 1 so it matches the stage shown in image 2: the mushrooms are gone, only the bark remains with a few small shrivelled translucent fragments lying on it. Aged and lifeless. {KEEP} {LOOK}.", "S10b")
print("pixie3b done", flush=True)
