"""Task 1381 (claude-wafer): staghorn coral (Acropora), Trent's 10-stage reef sequence through our flow.
Anchor P00: bare bark (klein text-to-image, seeds 7 11 23 42). v2: bark small in the lower quarter; P01-P06 chain; P07 and P08 branch from P06; P09-P10 chain from P08.
Output ~/var/claude-wafer-1380/pixie2/PNN_seed_S.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/reef"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
A = ("A small bare rounded rock of pale limestone reef rubble at the bottom centre of the frame, occupying only the lower quarter, with wide empty "
     "black space above it; seen from the front, isolated on a pure black background, no water, no bubbles, no seabed, no particles, macro nature "
     "photograph, broad soft light, real textures, sharp detail, nothing growing on it, no people, no text.")
ED = {1: (0, "a single tiny translucent pink coral larva has settled on the top of the rock, clearly visible"),
      2: (1, "the larva has become a single tiny coral polyp, a small pale tube with a crown of short tentacles, on the top of the rock"),
      3: (2, "a small juvenile staghorn coral colony, a cluster of short pale-brown nubs, now grows from the top of the rock"),
      4: (3, "the young staghorn coral has grown its first short branching antler-like tips, cream with purple-blue tips"),
      5: (4, "the staghorn coral colony has expanded into many upward branching antler-like arms, golden brown with violet-blue growing tips, rising high above the rock"),
      6: (5, "the staghorn coral is in vibrant mature form: a dense tall thicket of branching arms, rich golden-brown with bright electric-blue and violet tips, filling most of the frame"),
      7: (6, "tiny fluffy polyps are extended all over the staghorn branches, feeding, giving the arms a soft fuzzy look"),
      8: (6, "the polyps have retracted and the staghorn coral's colours have paled and faded toward cream"),
      9: (8, "the staghorn coral is losing its tissue: patches of bare bleached white skeleton spread along the branches, the remaining colour dull. Lifeless, not gory"),
      10: (9, "only the bare bleached white skeleton of the staghorn coral remains on the rock, chalky and brittle, a few broken branches. Lifeless")}
KEEP = "Keep the camera, framing, lighting, the rock's shape and position, and the pure black background exactly the same."
log = open(f"{B}/runs.jsonl", "a")
def run(cmd, key, p):
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True)
    log.write(json.dumps(dict(key=key, prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
    print(key, r.returncode, flush=True)
if not os.path.exists(f"{B}/P00_seed_42.png"):
    run([f"{H}/.local/bin/mflux-generate-flux2", "-m", "flux2-klein-4b", "-q", "8", "--prompt", A, "--seed", *SEEDS,
         "--width", "1024", "--height", "1024", "--output", f"{B}/P00.png"], "P00", A)
for s in SEEDS:
    for i in range(1, 11):
        frm, e = ED[i]; out = f"{B}/P{i:02d}_seed_{s}.png"
        if os.path.exists(out): continue
        p = f"The same rock; {e}. {KEEP}"
        run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/P{frm:02d}_seed_{s}.png",
             "--prompt", p, "--seed", s, "--output", out], f"P{i:02d}_seed_{s}", p)
print("reef done", flush=True)
