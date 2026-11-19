"""Task 1380 (claude-wafer): Trent's 10-stage waratah through our flow. FLUX.2 klein 4B q8 1024^2, seeds 7 11 23 42.
Pass 1: text-to-image for all ten stages (same base wording per seed).
Pass 2: per seed, chained edits from its full bloom (t07) to wilt, decay, dry remains (e08, e09, e10).
Output ~/var/claude-wafer-1380/waratah/{tNN,eNN}_seed_S.png, runs.jsonl."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/waratah"; os.makedirs(B, exist_ok=True)
SEEDS = ["7", "11", "23", "42"]
LOOK = ("Isolated on a pure black background, frontal view, centred, the short stem rising straight up from the bottom of the frame, "
        "whole subject in frame. Broad soft natural light, moderate depth of field, restrained highlights, real botanical textures, "
        "sharp detail, no wind blur, no bokeh, no halo, no soil, no pot, no people, no text.")
W = "an Australian New South Wales waratah (Telopea speciosissima)"
ST = [
    f"A single seed of {W}: one flat brown winged seed lying alone, small in the lower centre of the frame.",
    f"A tiny seedling of {W}: two small rounded green seed leaves on a short pale stem with fine roots, small in the lower centre of the frame.",
    f"A young plant of {W}: a short upright woody stem with a few leathery dark green serrated leaves, no flower yet.",
    f"{W[0].upper() + W[1:]} with a closed flower bud: a tight cone of overlapping green and rose-red bracts on a short upright stem, two leathery serrated leaves below.",
    f"{W[0].upper() + W[1:]} flower just opening: crimson bracts unfolding around a domed head of tightly packed red florets with green tips, on a short upright stem, two leathery serrated leaves below.",
    f"{W[0].upper() + W[1:]} in peak bloom: a large crimson domed flower head of curled florets, ringed by spreading red bracts, on a short upright stem, two leathery serrated leaves below.",
    f"{W[0].upper() + W[1:]} in full bloom: a large wide-open crimson flower head, every floret open and curled, red bracts spread wide, on a short upright stem, two leathery serrated leaves below.",
    f"{W[0].upper() + W[1:]} wilting: the flower head dull dark pink and slightly drooping, bracts curling at the edges, on a short upright stem, two leathery serrated leaves below.",
    f"{W[0].upper() + W[1:]} decaying: the flower head dried and shrivelled brown, bracts papery and brown, on a short upright stem, two dry curled leaves below. Aged, lifeless, not gory.",
    f"The dry remains of {W}: a small shrivelled brown dried flower head on a short dry stump. Aged, lifeless, not gory.",
]
ED = {8: "now wilting: the florets dull to a darker dusky pink and begin to droop, the bracts curl at their edges, the leaves sag slightly",
      9: "now decaying: the flower head dried, shrivelled and brown, the bracts papery and brown, the leaves dry and curled. Aged and lifeless, not gory",
      10: "now just the dry remains: the flower head collapsed into a small shrivelled brown husk, the bracts fallen away, the leaves withered. Aged and lifeless, not gory"}
KEEP = "Keep the camera, framing, lighting, stem position and pure black background exactly the same."
log = open(f"{B}/runs.jsonl", "a")
def run(cmd, rec):
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True)
    rec.update(rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")
    log.write(json.dumps(rec) + "\n"); log.flush(); print(rec["key"], r.returncode, rec["s"], flush=True)
for i, st in enumerate(ST, 1):
    key = f"t{i:02d}"
    if all(os.path.exists(f"{B}/{key}_seed_{s}.png") for s in SEEDS): continue
    p = f"{st} {LOOK}"
    run([f"{H}/.local/bin/mflux-generate-flux2", "-m", "flux2-klein-4b", "-q", "8", "--prompt", p, "--seed", *SEEDS,
         "--width", "1024", "--height", "1024", "--output", f"{B}/{key}.png"], dict(key=key, prompt=p, seeds=SEEDS))
for s in SEEDS:
    prev = f"{B}/t07_seed_{s}.png"
    for i in (8, 9, 10):
        out = f"{B}/e{i:02d}_seed_{s}.png"
        if not os.path.exists(out):
            p = f"The same waratah plant, {ED[i]}. {KEEP}"
            run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", prev,
                 "--prompt", p, "--seed", s, "--output", out], dict(key=f"e{i:02d}_seed_{s}", prompt=p, frm=prev))
        prev = out
print("waratah done", flush=True)
