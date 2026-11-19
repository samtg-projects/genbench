"""Task 1380, Mel's ending: dry remains -> soil -> mycelium threads. M1 text-to-image (seeds 7 11 23 42), M2-M4 chained klein edits.
Output ~/var/claude-wafer-1380/ending/{M1_seed_S, M2..M4_seed_S}.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/ending"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
LOOK = ("Isolated on a pure black background, frontal view, centred low in the frame, whole subject in frame. Broad soft natural light, "
        "moderate depth of field, real textures, sharp detail, no people, no text, not gory.")
M1 = ("A small low rounded mound of dark crumbly forest soil, with the dry shrivelled brown remains of a waratah flower head "
      "lying half sunk into its top. " + LOOK)
ED = {2: "now fine white mycelium threads begin to creep out of the soil and over the dry flower remains",
      3: "now the white mycelium has spread into a dense web of fine threads covering most of the mound, the flower remains almost gone into the soil",
      4: "now the flower remains are gone; only the soil mound remains, laced all over with a dense network of fine white mycelium threads"}
KEEP = "Keep the camera, framing, lighting, the mound's shape and the pure black background exactly the same."
log = open(f"{B}/runs.jsonl", "a")
def run(cmd, key, p):
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True)
    log.write(json.dumps(dict(key=key, prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
    print(key, r.returncode, flush=True)
if not os.path.exists(f"{B}/M1_seed_42.png"):
    run([f"{H}/.local/bin/mflux-generate-flux2", "-m", "flux2-klein-4b", "-q", "8", "--prompt", M1, "--seed", *SEEDS,
         "--width", "1024", "--height", "1024", "--output", f"{B}/M1.png"], "M1", M1)
for s in SEEDS:
    prev = f"{B}/M1_seed_{s}.png"
    for i in (2, 3, 4):
        out = f"{B}/M{i}_seed_{s}.png"
        if not os.path.exists(out):
            p = f"The same soil mound, {ED[i]}. {KEEP}"
            run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", prev,
                 "--prompt", p, "--seed", s, "--output", out], f"M{i}_seed_{s}", p)
        prev = out
print("ending done", flush=True)
