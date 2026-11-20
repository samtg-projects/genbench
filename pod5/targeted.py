"""Task 1383 step 4, round 2: targeted in-betweens at the big jumps only. Each is a klein edit of the EARLIER stage with a concrete
description of the intermediate state ('halfway' alone snapped to an end or invented subjects). Output dir/T_<a>_<b>[n]_seed_S.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); V = f"{H}/var/claude-wafer-1380"; ED = f"{H}/.local/bin/mflux-generate-flux2-edit"
KEEP = "Keep the camera, framing, scale, the anchor's exact shape and position, and the pure black background exactly the same. Photorealistic."
JOBS = [  # dir, seed, from-key, out-name, description
    ("pixie2", "11", "P04", "T_P04_P05a", "the three blue-tipped stalks have grown taller, about half their final height, each now topped by a small closed deep-blue bud cap"),
    ("pixie2", "11", "T_P04_P05a", "T_P04_P05b", "the three stalks are now nearly full height with small bell-shaped cyan-blue caps just starting to open"),
    ("pixie2", "11", "P05", "T_P05_P06", "the three cyan caps have opened halfway, wider bells, not yet the full flat parasols"),
    ("ghost", "23", "Q05", "T_Q05_P06a", "the young ivory fans have grown larger and more numerous, overlapping, about half the size of a full cluster, gills faintly green"),
    ("ghost", "23", "T_Q05_P06a", "T_Q05_P06b", "the ivory fan cluster is now about three quarters of its full size, wide wavy fans spreading, gills glowing faintly green"),
    ("lorikeet", "23", "L09", "T_L09_L10", "the young lorikeet's colours are halfway to adult: the violet-blue head and orange breast brighter but the green wings still dull. There is only this one bird"),
    ("lorikeet", "23", "L06", "T_L06_L07", "the grey downy nestling is a little bigger, the first coloured pin feathers just showing on its wings. There is only this one chick, in the nest"),
]
for d, s, frm, name, desc in JOBS:
    B = f"{V}/{d}"; out = f"{B}/{name}_seed_{s}.png"
    if os.path.exists(out): continue
    src = f"{B}/{frm}_seed_{s}.png"; p = f"The same scene; {desc}. {KEEP}"; t0 = time.time()
    r = subprocess.run([ED, "-m", "flux2-klein-4b", "-q", "8", "--image-paths", src, "--prompt", p, "--seed", s, "--output", out], capture_output=True, text=True)
    open(f"{B}/runs.jsonl", "a").write(json.dumps(dict(key=name, prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n")
    print(name, r.returncode, flush=True)
print("targeted done", flush=True)
