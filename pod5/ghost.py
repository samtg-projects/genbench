"""Task 1381 (claude-wafer): ghost fungus (Omphalotus nidiformis), Trent's 10-stage fungi sequence through our flow.
Anchor P00: bare bark (klein text-to-image, seeds 7 11 23 42). v2: bark small in the lower quarter; P01-P06 chain; P07 and P08 branch from P06; P09-P10 chain from P08.
Output ~/var/claude-wafer-1380/ghost/PNN_seed_S.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/ghost"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
A = ("A short low stub of a rotting eucalyptus log lying on its side at the bottom centre of the frame, occupying only the lower quarter, with wide empty "
     "black space above it; seen from the front at a low angle, isolated on a pure black background, macro nature photograph, broad soft light, real textures, sharp detail, nothing growing on it, "
     "no mushrooms, no plants, no people, no text.")
ED = {1: (0, "a small cluster of tiny pale cream spores now rests on the top of the log, clearly visible"),
      2: (1, "the cream spores are sprouting short bright white threads, clearly visible"),
      3: (2, "bright white branching mycelium threads now spread clearly across the log's top and side like frost"),
      4: (3, "a few small rounded cream knobs, the beginnings of ghost fungus, now push out of the side of the log"),
      5: (4, "the knobs have grown into small young ghost fungus caps: pale cream fan-shaped shelves curling outward from the side of the log"),
      6: (5, "the ghost fungus is fully mature: a large overlapping cluster of wide ivory-white fan-shaped caps with wavy edges spreading from the log, the gills beneath softly glowing a faint luminous green"),
      7: (6, "a few tiny pale spore specks drift just beneath the ivory caps; nothing else changes"),
      8: (6, "the ghost fungus is ageing: the ivory caps yellow and darken at their edges, curling, the faint green glow fading"),
      9: (8, "the ghost fungus is decomposing: the caps collapsed, shrivelled and brown, drooping against the log. Aged and lifeless, not gory"),
      10: (9, "the fungus is gone; only the log with its white mycelium remains. Aged and lifeless")}
KEEP = "Keep the camera, framing, lighting, the log's shape and position, and the pure black background exactly the same."
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
        p = f"The same log stub; {e}. {KEEP}"
        run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/P{frm:02d}_seed_{s}.png",
             "--prompt", p, "--seed", s, "--output", out], f"P{i:02d}_seed_{s}", p)
print("ghost done", flush=True)
