"""Task 1380 ending, more mycelium: M5, M6 chained klein edits from M4 (seeds 7, 11)."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/ending"
ED = {5: "now a dense web of bright white mycelium threads covers the whole mound, clearly visible, fine branching filaments",
      6: "now the bright white mycelium threads also reach out from the base of the mound in fine branching strands across the black, like roots of light"}
KEEP = "Keep the camera, framing, lighting, the mound's shape and the pure black background exactly the same."
log = open(f"{B}/runs.jsonl", "a")
for s in ["7", "11"]:
    prev = f"{B}/M4_seed_{s}.png"
    for i in (5, 6):
        out = f"{B}/M{i}_seed_{s}.png"; p = f"The same soil mound, {ED[i]}. {KEEP}"; t0 = time.time()
        r = subprocess.run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", prev,
                            "--prompt", p, "--seed", s, "--output", out], capture_output=True, text=True)
        log.write(json.dumps(dict(key=f"M{i}_seed_{s}", prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
        prev = out
print("ending2 done", flush=True)
