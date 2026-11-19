"""Task 1381 (claude-wafer): pixie parasol (Mycena interrupta), Trent's 10-stage fungi sequence through our flow.
Anchor P00: bare bark (klein text-to-image, seeds 7 11 23 42). v2: bark small in the lower quarter; P01-P06 chain; P07 and P08 branch from P06; P09-P10 chain from P08.
Output ~/var/claude-wafer-1380/pixie2/PNN_seed_S.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/pixie2"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
A = ("A small chip of rotting eucalyptus bark lying flat at the bottom centre of the frame, occupying only the lower quarter, with wide empty "
     "black space above it; seen from the front at a low angle, isolated on a pure black background, macro nature photograph, broad soft light, real textures, sharp detail, nothing growing on it, "
     "no mushrooms, no plants, no people, no text.")
ED = {1: (0, "a small cluster of tiny glistening pale-blue spore grains now sits in the centre of the bark, clearly visible"),
      2: (1, "the pale-blue spore grains are sprouting short bright white threads, clearly visible"),
      3: (2, "bright white branching mycelium threads now spread clearly across the whole top of the bark like frost"),
      4: (3, "three small slender white stalks with round deep-blue knob tips now rise from the centre of the bark, about a third of the frame tall"),
      5: (4, "the three stalks have grown tall into young pixie parasol mushrooms rising high above the bark: tall slender translucent white stems and bell-shaped cyan-blue caps"),
      6: (5, "the caps have opened wide into large ribbed translucent cyan-blue parasols with deep-blue centres and fine gills; the three mushrooms fill most of the frame above the bark"),
      7: (6, "a few tiny pale spore specks are falling just beneath each cap; nothing else changes"),
      8: (6, "the three pixie parasol mushrooms are ageing: the caps fade to a pale washed-out blue-grey, their edges curling and splitting, the stems leaning slightly"),
      9: (8, "the three mushrooms are decomposing: collapsed, shrivelled, translucent brown, caps drooping and torn. Aged and lifeless, not gory"),
      10: (9, "the mushrooms are gone; only the bark with its white mycelium remains, with a few tiny shrivelled fragments. Aged and lifeless")}
KEEP = "Keep the camera, framing, lighting, the bark's shape and position, and the pure black background exactly the same."
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
        p = f"The same piece of bark; {e}. {KEEP}"
        run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/P{frm:02d}_seed_{s}.png",
             "--prompt", p, "--seed", s, "--output", out], f"P{i:02d}_seed_{s}", p)
print("pixie done", flush=True)
