"""Task 1381 (claude-wafer): pixie parasol (Mycena interrupta), Trent's 10-stage fungi sequence through our flow.
Anchor P00: bare bark (klein text-to-image, seeds 7 11 23 42). P01-P03 are edits straight from P00; P04-P07 chain from P03;
P08-P10 chain from P07. Output ~/var/claude-wafer-1380/pixie/PNN_seed_S.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/pixie"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
A = ("A small flat piece of rotting eucalyptus bark and decayed wood lying flat, seen from the front at a low angle, isolated on a pure black "
     "background, centred low in the frame, macro nature photograph, broad soft light, real textures, sharp detail, nothing growing on it, "
     "no mushrooms, no plants, no people, no text.")
ED = {1: (0, "a few tiny clusters of pale translucent blue spores now rest on its surface"),
      2: (0, "tiny pale translucent blue spores on its surface are now sprouting fine white thread-like hyphae"),
      3: (0, "a fine white branching mycelium now spreads across its surface like frost"),
      4: (3, "three tiny slender white stalks with small round deep-blue tips now rise from the mycelium, the beginnings of pixie parasol mushrooms"),
      5: (4, "the three stalks have grown into young pixie parasol mushrooms: slender translucent white stems topped by small bell-shaped cyan-blue caps"),
      6: (5, "the three pixie parasol mushrooms are fully mature: tall slender white stems and wide open ribbed translucent cyan-blue caps with deep blue centres and fine gills"),
      7: (6, "a faint compact haze of fine pale spores now drifts just beneath the three cyan-blue caps"),
      8: (7, "the three pixie parasol mushrooms are ageing: the caps fade to a pale washed-out blue, their edges curling and splitting, the stems leaning"),
      9: (8, "the three mushrooms are decomposing: collapsed, shrivelled and translucent brown, caps drooping and torn. Aged and lifeless, not gory"),
      10: (9, "the mushrooms are gone; only a few small shrivelled translucent fragments remain on the bark. Aged and lifeless")}
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
