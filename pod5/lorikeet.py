"""Task 1381 (claude-wafer): rainbow lorikeet (Trichoglossus moluccanus), Trent's 20-frame bird branch through our flow.
Anchor A: a bare host twig (Melicope elleryana) with glossy leaves, klein text-to-image, seeds 7 11 23 42. Every frame is an edit
of A or of a short chain from it, so the twig and its key leaf hold fixed coordinates. Output ~/var/claude-wafer-1380/lorikeet/."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/lorikeet"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
A = ("A short horizontal eucalyptus branch across the lower middle of the frame: at its left end a small round cup nest woven from twigs and bark, "
     "at its right end a cluster of bright red flowering gum blossom with a few leaves. Isolated on a pure black background, frontal view, broad soft "
     "light, nature photograph, real textures, sharp detail, empty space above the branch, the nest empty, no birds, no people, no text.")
U = "a rainbow lorikeet"
ED = [  # key, from, edit
    ("L01", "A", "two small white eggs now lie in the nest"),
    ("L02", "L01", "one of the two eggs now has a fine first crack in its shell"),
    ("L03", "L02", "a tiny orange beak tip now pokes through the cracked egg"),
    ("L04", "L03", "the egg has broken open and a pink, featherless newborn chick is struggling out of the shell"),
    ("L05", "L04", "a tiny pink bare hatchling now lies in the nest beside the broken eggshell and the other egg"),
    ("L06", "L05", "the chick has grown into a fluffy grey downy nestling with an orange beak, sitting up in the nest"),
    ("L07", "L06", "the nestling is bigger, with pin feathers coming through in green, blue and orange patches, its head above the nest rim"),
    ("L08", "A", f"a young {U[2:]} with duller, patchy juvenile colours now perches on the branch beside the empty nest"),
    ("L09", "L08", "the young lorikeet's colours have brightened: a blue head, an orange-red breast and green wings"),
    ("L10", "L09", "the lorikeet is now a vivid adult: deep violet-blue head, bright red-orange and yellow breast, rich green wings and long tail"),
    ("L11", "L10", "the adult lorikeet stretches its wings out wide, showing the red and yellow bands under them, still gripping the branch"),
    ("L12", "L11", "the lorikeet is taking off, lifting just above the branch with its wings raised high"),
    ("L13", "A", f"{U} swoops in toward the red gum blossom, wings spread, about to land"),
    ("L14", "L13", "the lorikeet has landed on the branch beside the red gum blossom, wings folded"),
    ("L15", "L14", "the lorikeet leans into the red blossom, its beak buried in the flowers, feeding on nectar"),
    ("L16", "L15", "the lorikeet lifts off from the blossom, wings raised, departing"),
    ("L17", "A", f"{U} flies away in the distance, small in the upper right of the frame, wings spread"),
]
KEEP = "Keep the camera, framing, lighting, the branch, nest and blossom exactly where they are, and the pure black background, the same."
log = open(f"{B}/runs.jsonl", "a")
def run(cmd, key, p):
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True)
    log.write(json.dumps(dict(key=key, prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
    print(key, r.returncode, flush=True)
if not os.path.exists(f"{B}/A_seed_42.png"):
    run([f"{H}/.local/bin/mflux-generate-flux2", "-m", "flux2-klein-4b", "-q", "8", "--prompt", A, "--seed", *SEEDS,
         "--width", "1024", "--height", "1024", "--output", f"{B}/A.png"], "A", A)
for s in SEEDS:
    for key, frm, e in ED:
        out = f"{B}/{key}_seed_{s}.png"
        if os.path.exists(out): continue
        p = f"The same branch; {e}. {KEEP}"
        run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/{frm}_seed_{s}.png",
             "--prompt", p, "--seed", s, "--output", out], f"{key}_seed_{s}", p)
print("lorikeet done", flush=True)
