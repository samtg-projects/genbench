"""Task 1381 ghost fungus fixes (seeds 11, 23): Q04 primordia and Q05 emergence chained from P03 with emphatic wording;
Q09 decomposition from P08. Output ~/var/claude-wafer-1380/ghost/QNN_seed_S.png."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/ghost"
KEEP = "Keep the camera, framing, lighting, the log's shape and position, and the pure black background exactly the same."
ED = [("Q04", "P03", "five small rounded creamy-white knobs, clearly visible, each the size of a fingertip, now push out from the side of the log"),
      ("Q05", "Q04", "the knobs have grown into a cluster of young ghost fungus caps, clearly visible: small ivory-white fan-shaped shelves about a quarter of the log's width, curling outward from the side of the log, gills faintly green"),
      ("Q09", "P08", "the fungus cluster has collapsed and rotted: the caps shrunken, wrinkled, dark brown and slumped flat against the log, no glow. Aged and lifeless, not gory")]
log = open(f"{B}/runs.jsonl", "a")
for s in ["11", "23"]:
    for key, frm, e in ED:
        out = f"{B}/{key}_seed_{s}.png"; p = f"The same log stub; {e}. {KEEP}"; t0 = time.time()
        r = subprocess.run([f"{H}/.local/bin/mflux-generate-flux2-edit", "-m", "flux2-klein-4b", "-q", "8", "--image-paths", f"{B}/{frm}_seed_{s}.png",
                            "--prompt", p, "--seed", s, "--output", out], capture_output=True, text=True)
        log.write(json.dumps(dict(key=f"{key}_seed_{s}", prompt=p, rc=r.returncode, s=round(time.time() - t0, 1), err=r.stderr[-300:] if r.returncode else "")) + "\n"); log.flush()
print("ghost_fix done", flush=True)
