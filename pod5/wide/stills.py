"""Task 1384 (claude-producer): Trent's rock (05), chameleon (08), strangler fig (02), iris (06) and the 12 standalone
flowers, through our flow. Every anchor is a klein edit of Trent's own frame (crops of files 3084-3093 in CROPS), and every
later stage is an edit of the anchor or of the stage before, with Trent's matching frame as a second reference where
that helps. Output ~/var/claude-producer-1384/<branch>/NAME_seed_S.png, runs.jsonl beside it.

    stills.py anchors                 every branch's anchor (two seeds), the 12 flowers, and the chameleon skin test
    stills.py chain <branch> <seed>   one branch's stages off its picked anchor
"""
import json, os, shutil, subprocess, sys, time
H = os.path.expanduser("~"); ROOT = f"{H}/var/claude-producer-1384"; CROPS = f"{ROOT}/crops"
BIN = f"{H}/.local/bin"; SEEDS = ["7", "23"]
BLACK = "isolated on a pure black background, broad soft light, real textures, sharp detail, no people, no text"


def run(cmd, out, prompt):
    if os.path.exists(out):
        return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True)
    with open(f"{os.path.dirname(out)}/runs.jsonl", "a") as log:
        log.write(json.dumps(dict(out=os.path.basename(out), prompt=prompt, rc=r.returncode, s=round(time.time() - t0, 1),
                                  err=r.stderr[-300:] if r.returncode else "")) + "\n")
    print(os.path.basename(out), r.returncode, round(time.time() - t0, 1), flush=True)


def edit(images, prompt, seed, out, size=True):
    run([f"{BIN}/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", *images, "--prompt", prompt,
         "--seed", seed, *(["--width", "1024", "--height", "1024"] if size else []), "--output", out], out, prompt)


# ---- 08 chameleon: twenty skins on one pose ------------------------------------------------------------------
CHAM_ANCHOR = ("Recreate this chameleon as a crisp, high-detail stylised 3D character: exactly this pose and direction, walking along "
               "this mossy log, its curled tail, raised front foot and large friendly eye exactly as shown, rainforest emerald green "
               "skin with lighter lime stripes. The whole chameleon and the whole log in frame, centred, seen from the side, with a "
               f"margin all round, {BLACK}.")
SKINS = ["rainforest emerald green with lighter lime stripes", "deep cobalt blue scattered with glowing cyan bioluminescent dots",
         "vivid neon magenta blending into electric cyan", "swirling amber, orange and magenta psychedelic marbling",
         "a soft, velvety covering of bright green moss", "pale grey-green leafy foliose lichen",
         "crusty bright orange crustose lichen patches over pale grey-green", "overlapping soft pink flower petals like scales",
         "crimson red waratah bracts and curled florets", "overlapping blue-green eucalyptus leaves",
         "rows of bright green fern pinnae", "glossy wet dark-brown bark with fine ridges",
         "cracked ochre sandstone", "milky white opal with rainbow iridescent flashes",
         "butterfly wing scales in orange, black and iridescent blue", "clusters of orange and coral-pink coral polyps",
         "peach and cream mushroom gills and small caps", "jade green beaded with clear dew drops",
         "a dusting of golden pollen over warm yellow-gold", "midnight blue swept with green and violet aurora bands"]
KEEP_CHAM = "Keep the pose, the eye, the mossy log, the camera, the framing, the lighting and the pure black background exactly the same."
def cham_skin2(k, seed, anchor, out):   # anchor + Trent's frame k as the skin reference
    edit([anchor, f"{CROPS}/cham{k:02d}.png"], f"Give the chameleon in the first image the skin of the chameleon in the second image: "
         f"{SKINS[k - 1]}, over its whole body, head, crest, legs and tail. {KEEP_CHAM}", seed, out)
def cham_skin1(k, seed, anchor, out):   # anchor and words only
    edit([anchor], f"The same chameleon, with its skin changed to {SKINS[k - 1]}, over its whole body, head, crest, legs and tail. "
         f"{KEEP_CHAM}", seed, out)

# ---- 06 iris: one fictional iris, ten frames -------------------------------------------------------------------
IRIS_ANCHOR = ("A single fictional iris seen straight on, filling most of the frame: exactly this iris pattern, slate-blue fibres "
               "radiating from a golden-orange collarette ring, a round black pupil of medium size in the centre. Macro photograph, "
               "sharp fibre detail, soft even light, the iris disc isolated on a pure black background, no eyelid, no lashes, no "
               "skin, no reflections, no people, no text.")
KEEP_IRIS = "Keep the iris pattern, its colours, its size and position, the camera and the pure black background exactly the same."
IRIS = {2: (2, "The pupil has contracted slightly and is a little smaller."), 3: (3, "The pupil has contracted to a small dot."),
        4: (4, "Warm golden light now grazes the iris from the upper left, raising the relief of its fibres; the pupil is medium."),
        6: (6, "The pupil has dilated slightly and is a little larger than medium."),
        7: (7, "The pupil is dilated wide, about half the width of the iris."),
        8: (8, "Cool blue-white light now comes from the right side, with one small soft highlight on the iris; the pupil is medium."),
        9: (9, "The pupil is medium and the eye has shifted its gaze very slightly to the left.")}

# ---- 05 rock: the rock once, then the moss zone ---------------------------------------------------------------
ROCK_ANCHOR = ("This exact rock, bare: remove every plant, fern, moss and lichen, leaving only the weathered ochre, rust and grey "
               "sandstone rock with its cracks and ledges. The whole rock centred, with empty space above it and a margin all round, "
               f"{BLACK}.")
KEEP_ROCK = "Keep the rock's shape, colour, cracks and position, the camera, the framing, the lighting and the pure black background exactly the same."
MOSS = ["a tiny tuft of bright green moss has arrived on the flat upper-left ledge of the rock",
        "the moss on the upper-left ledge is establishing: a small loose patch of fine green shoots",
        "the moss on the upper-left ledge is in early growth: a low spreading mat of green shoots",
        "the moss on the upper-left ledge has expanded into a rounded green cushion with a few thin brown stalks",
        "the moss cushion on the upper-left ledge is maturing: larger, dense and bright lime green, with many thin stalks and small capsules",
        "the moss cushion on the upper-left ledge is at peak growth: big, lush and bright lime green, with many stalks and capsules",
        "the moss cushion on the upper-left ledge holds at maturity: big, lush and bright green with capsules",
        "the moss cushion on the upper-left ledge is ageing: its green fading to yellow-olive, its stalks bending",
        "the moss cushion on the upper-left ledge is decaying: shrunken, dry and brown. Lifeless, not gory",
        "only a tiny dry remnant tuft of moss is left on the upper-left ledge, the rest of the ledge bare again"]
MOSS_FROM = [0, 1, 2, 3, 4, 5, 6, 6, 8, 9]          # stage k is an edit of stage MOSS_FROM[k-1] (0 = the bare rock)

# ---- 02 strangler fig, ground up ------------------------------------------------------------------------------
FIG_ANCHOR = ("A small flat patch of dark rainforest soil and leaf litter at the bottom centre of the frame, occupying only the bottom "
              "strip, with wide empty black space above it, seen from the front at a low angle, nothing growing on it, "
              f"{BLACK}.")
KEEP_FIG = "Keep the soil patch, the camera, the framing, the lighting and the pure black background exactly the same."
FIG = ["a single smooth brown fig seed lies on the soil",
       "the fig seed has split: a pale root reaches into the soil and a tiny green shoot rises from it",
       "a small fig seedling with two glossy leaves stands on the soil, its fine roots visible at its base",
       "a slender fig sapling about knee high, with several glossy dark-green leaves, grows from the soil",
       "a young strangler fig tree grows from the soil: a braided lattice of pale aerial roots around its trunk and a rounded leafy crown, filling half the frame",
       "a huge mature strangler fig: a massive braided lattice of pale roots spreading into buttresses over the soil, rising into a broad dense green canopy that fills the frame",
       "the same huge mature strangler fig in soft late light, every root of its lattice and every leaf of its canopy in sharp detail",
       "the strangler fig is ageing into a snag: its canopy thinned to sparse leaves and bare grey branches, its root lattice weathered grey",
       "only a low broken stump of weathered root lattice and fallen wood remains on the soil, mossy and decaying. Lifeless, not gory",
       "only a small mossy piece of rotting wood remains on the soil, with one new fig seedling sprouting from it"]
FIG_FROM = [0, 1, 2, 3, 4, 5, 6, 6, 8, 9]

# ---- stretch: Trent's 12 standalone flowers ---------------------------------------------------------------------
FLOWERS = ["waratah", "scarlet banksia", "kangaroo paw", "Sturt's desert pea", "flannel flower", "golden everlasting",
           "pink paper daisy", "blue lechenaultia", "firewheel tree flower", "red flowering gum blossom", "golden wattle",
           "Cooktown orchid"]
def flower(k, seed="7"):
    edit([f"{CROPS}/flower{k:02d}.png"], f"Recreate this {FLOWERS[k - 1]} as a photoreal macro nature photograph: the whole flower "
         "head with its short stem and attached leaves exactly as shown, centred and filling most of the frame, seen from the front, "
         "isolated on a pure black background, broad natural light, restrained highlights, real textures, sharp detail, "
         "no people, no text.", seed, f"{ROOT}/flowers/W{k:02d}_seed_{seed}.png")


def anchors():
    for s in SEEDS:
        edit([f"{CROPS}/cham01.png"], CHAM_ANCHOR, s, f"{ROOT}/cham/C00_seed_{s}.png")
        cham_skin2(2, s, f"{ROOT}/cham/C00_seed_{s}.png", f"{ROOT}/cham/test2_C02_seed_{s}.png")
        cham_skin1(2, s, f"{ROOT}/cham/C00_seed_{s}.png", f"{ROOT}/cham/test1_C02_seed_{s}.png")
        edit([f"{CROPS}/iris01.png"], IRIS_ANCHOR, s, f"{ROOT}/iris/I00_seed_{s}.png")
        edit([f"{CROPS}/rock.png"], ROCK_ANCHOR, s, f"{ROOT}/rock/K00_seed_{s}.png")
        edit([f"{CROPS}/fig01.png"], FIG_ANCHOR, s, f"{ROOT}/fig/G00_seed_{s}.png")
    for k in range(1, 13):
        flower(k)


def chain(branch, s, two=True):
    d = f"{ROOT}/{branch}"
    if branch == "cham":
        a = f"{d}/C00_seed_{s}.png"
        for k in range(1, 21):
            (cham_skin2 if two else cham_skin1)(k, s, a, f"{d}/C{k:02d}_seed_{s}.png")
    elif branch == "iris":
        a = f"{d}/I00_seed_{s}.png"
        for k, (ref, e) in IRIS.items():
            edit([a, f"{CROPS}/iris{ref:02d}.png"] if two else [a], f"The same iris. {e} {KEEP_IRIS}", s, f"{d}/I{k:02d}_seed_{s}.png")
    elif branch in ("rock", "fig"):
        P, FROM, KEEP, tag, ref = (MOSS, MOSS_FROM, KEEP_ROCK, "K", "moss") if branch == "rock" else (FIG, FIG_FROM, KEEP_FIG, "G", "fig")
        for k in range(1, 11):
            src = f"{d}/{tag}{FROM[k - 1]:02d}_seed_{s}.png"
            what = "rock" if branch == "rock" else "soil patch"
            edit([src, f"{CROPS}/{ref}{k:02d}.png"] if two else [src],
                 f"The same {what}; {P[k - 1]}" + (", like the second image" if two else "") + f". {KEEP}", s, f"{d}/{tag}{k:02d}_seed_{s}.png")


# v2 of fig stages 5-10: the first chain held the sapling's leaves and then returned stage 6 unchanged four times.
FIG2 = {5: ("G04", "the sapling has grown into a young strangler fig tree: a braided lattice of pale aerial roots wraps its trunk and a "
            "rounded leafy crown of small leaves spreads above, filling the upper half of the frame; no large glossy leaves"),
        6: ("G05", "the strangler fig is now huge and mature: a massive braided lattice of pale roots flares into buttresses over the soil "
            "and rises into a broad, dense green canopy that fills the whole upper frame"),
        8: ("G06", "every leaf is gone: the strangler fig is now a dead, ageing snag, a weathered grey lattice of roots with bare grey "
            "branches and no green leaves at all"),
        9: ("G00", "only a low, broken, mossy stump of weathered grey strangler-fig root lattice and fallen wood lies on the soil, waist "
            "high at most. Lifeless, not gory"),
        10: ("G00", "a small mossy piece of rotting wood lies on the soil, and one new fig seedling with two leaves sprouts from it")}
def fig2(s):
    d = f"{ROOT}/fig"
    for k, (frm, e) in FIG2.items():
        src = f"{d}/{frm}_seed_{s}.png" if frm == "G00" or k <= 6 else f"{d}/v2_{frm}_seed_{s}.png"
        if frm in ("G05",) : src = f"{d}/v2_G05_seed_{s}.png"
        if frm in ("G06",) : src = f"{d}/v2_G06_seed_{s}.png"
        edit([src, f"{CROPS}/fig{k:02d}.png"], f"The same soil patch; {e}, like the second image. {KEEP_FIG}", s, f"{d}/v2_G{k:02d}_seed_{s}.png")
    shutil.copy(f"{d}/v2_G06_seed_{s}.png", f"{d}/v2_G07_seed_{s}.png")


# Miniature fig stages 5-9 (Trent, doc 671: the big canopy looked "jank" at 30k; a miniature rather than a canopy).
FIGM = {5: ("G04", "the sapling has grown into a small young strangler fig, a miniature tree only a little taller than the sapling: a short "
            "trunk wrapped in a few thick pale braided roots and a small rounded crown of clustered glossy leaves; compact, simple shapes"),
        6: ("m05", "the miniature strangler fig is now mature: its pale braided roots have thickened into a sturdy root cage flaring over "
            "the soil, and its small dense rounded crown is a little fuller; still a miniature, about the same height, compact and simple"),
        8: ("m06", "every leaf is gone: the miniature strangler fig is now a dead grey snag, a small weathered grey cage of braided roots "
            "with a few short bare branches"),
        9: ("G00", "only a low, broken, mossy stump of weathered grey braided fig root and one piece of fallen wood lie on the soil. "
            "Lifeless, not gory")}
def figm(s):
    d = f"{ROOT}/fig"
    for k, (frm, e) in FIGM.items():
        src = f"{d}/{frm}_seed_{s}.png" if frm.startswith("G") else f"{d}/{frm.replace('m', 'mini_G')}_seed_{s}.png"
        edit([src, f"{CROPS}/fig{k:02d}.png"], f"The same soil patch; {e}. {KEEP_FIG}", s, f"{d}/mini_G{k:02d}_seed_{s}.png")
    shutil.copy(f"{d}/mini_G06_seed_{s}.png", f"{d}/mini_G07_seed_{s}.png")


if __name__ == "__main__":
    if sys.argv[1] == "anchors":
        anchors()
    elif sys.argv[1] == "figm":
        figm(sys.argv[2])
    elif sys.argv[1] == "fig2":
        fig2(sys.argv[2])
    else:
        chain(sys.argv[2], sys.argv[3], two=(len(sys.argv) < 5 or sys.argv[4] != "one"))
    print("done", flush=True)
