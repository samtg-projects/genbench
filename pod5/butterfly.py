"""Task 1381 (claude-wafer): Ulysses butterfly (Papilio ulysses), Trent's 20 frames through our flow.
Anchor A: a bare host twig (Melicope elleryana) with glossy leaves, klein text-to-image, seeds 7 11 23 42. Every frame is an edit
of A or of a short chain from it, so the twig and its key leaf hold fixed coordinates. Output ~/var/claude-wafer-1380/butterfly/."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/butterfly"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
A = ("A single slender woody twig of the Australian rainforest tree Melicope elleryana, held diagonally across the lower half of the frame, with "
     "three glossy oval green leaves, one larger key leaf near its right end. Isolated on a pure black background, frontal view, broad soft light, "
     "macro nature photograph, real textures, sharp detail, empty space above the twig, nothing on the twig, no people, no text.")
U = "an Ulysses swallowtail"
ED = [  # key, from, edit
    ("B01", "A", "a small young swallowtail caterpillar, mottled brown and white like a bird dropping, now rests at the left end of the twig"),
    ("B02", "B01", "the caterpillar has grown a little and turned green with pale saddle markings, climbing along the twig toward the key leaf"),
    ("B03", "B02", "the green caterpillar now reaches the key leaf and takes a first bite from its edge"),
    ("B04", "B03", "the key leaf now has several ragged holes eaten through it, the green caterpillar beside them"),
    ("B05", "B04", "the green caterpillar has grown larger and plumper, with bold white and olive saddle bands, still feeding on the holed leaf"),
    ("B06", "B05", "the caterpillar is now a fat mature larva, bright green with white bands and small eyespots, lying along the twig"),
    ("B07", "B06", "the mature caterpillar hunches up, its front end raised, preparing to pupate"),
    ("B08", "B07", "the caterpillar has shortened and curled tight against the twig, held by a pale silk pad, its skin dull"),
    ("B09", "A", "a fresh smooth bright-green swallowtail chrysalis, angular with a pointed tip, now hangs upright from the twig near the key leaf, attached by a silk girdle; a butterfly chrysalis, not a cocoon"),
    ("B10", "B09", "the chrysalis is now mature and translucent, the folded electric-blue and black wings of the butterfly visible through its thin casing"),
    ("B11", "B10", "the chrysalis casing has split open along its front, the dark butterfly inside starting to push out"),
    ("B12", "B11", f"{U} butterfly is emerging from the split casing, clinging to it, its wings still small, soft and crumpled"),
    ("B13", "A", f"{U} butterfly now perches on the twig near the key leaf, its wings half expanded, still soft, electric-blue patches bordered in black"),
    ("B14", "B13", "the butterfly's wings are now fully expanded and spread open flat: brilliant electric-blue centres with wide velvety black borders and tails"),
    ("B15", "B14", "the butterfly has lifted just above the twig in flight, its wings swept down on the downstroke"),
    ("B16", "B15", "the butterfly flies higher above the twig, its wings raised high on the upstroke"),
    ("B17", "A", f"{U} butterfly is landing on the twig, its wings closed upright, showing the dark brown undersides with a flash of blue at the edge"),
    ("B18", "B17", "the butterfly rests quietly on the twig, wings closed upright, legs gripping the twig"),
    ("B19", "B14", "the butterfly is old: its open wings are faded to a dull pale blue, scales worn, the edges frayed and torn"),
    ("B20", "B19", "the butterfly has died: it lies collapsed along the twig, its faded wings crumpled and torn. Aged and lifeless, not gory"),
]
KEEP = "Keep the camera, framing, lighting, the twig and its leaves exactly where they are, and the pure black background, the same."
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
        p = f"The same twig; {e}. {KEEP}"
        run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/{frm}_seed_{s}.png",
             "--prompt", p, "--seed", s, "--output", out], f"{key}_seed_{s}", p)
print("butterfly done", flush=True)
