"""Task 1380: waratah stages 5-10 as chained klein edits from each seed's text-to-image closed bud (t04).
Output ~/var/claude-wafer-1380/waratah/cNN_seed_S.png (c04 = copy of t04)."""
import json, os, shutil, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/waratah"
SEEDS = ["7", "11", "23", "42"]
KEEP = "Keep the camera, framing, lighting, stem, leaves and pure black background exactly the same."
ED = {5: "now opening: the crimson bracts unfold outward and the bud swells into a rounded head of tightly packed red florets",
      6: "now in peak bloom: the head has become a broad rounded crimson dome, wider than it is tall, made of hundreds of curled red florets, ringed at its base by large spreading red bracts",
      7: "now in full bloom: the broad crimson dome is fully open, every floret curled outward, the red bracts spread wide and flat",
      8: "now wilting: the florets dull to a darker dusky pink and begin to droop, the bracts curl at their edges, the leaves sag slightly",
      9: "now decaying: the flower head has dried, shrivelled and turned brown, the bracts papery and brown, the leaves dry and curled. Aged and lifeless, not gory",
      10: "now just the dry remains: the flower head collapsed into a small shrivelled brown husk, the bracts fallen away, the leaves withered and brown. Aged and lifeless, not gory"}
log = open(f"{B}/runs.jsonl", "a")
for s in SEEDS:
    shutil.copy(f"{B}/t04_seed_{s}.png", f"{B}/c04_seed_{s}.png"); prev = f"{B}/c04_seed_{s}.png"
    for i in range(5, 11):
        out = f"{B}/c{i:02d}_seed_{s}.png"
        if not os.path.exists(out):
            p = f"The same waratah plant, {ED[i]}. {KEEP}"; t0 = time.time()
            r = subprocess.run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", prev,
                                "--prompt", p, "--seed", s, "--output", out], capture_output=True, text=True)
            log.write(json.dumps(dict(key=f"c{i:02d}_seed_{s}", prompt=p, frm=prev, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
            print(f"c{i:02d}_seed_{s}", r.returncode, flush=True)
        prev = out
print("chain done", flush=True)
