"""Task 1380: the waratah seed stage again, without the upright-stem framing (klein 4B q8, seeds 7 11 23 42)."""
import json, os, subprocess, time
H = os.path.expanduser("~"); B = f"{H}/var/claude-wafer-1380/waratah"
p = ("A single seed of an Australian New South Wales waratah (Telopea speciosissima): one small flat oval brown seed with a thin papery wing, "
     "lying on its side, alone, seen from the front, small in the lower centre of the frame. Isolated on a pure black background, no stem, no stalk, "
     "no plant, no soil. Broad soft natural light, moderate depth of field, real botanical texture, sharp detail, no people, no text.")
t0 = time.time()
r = subprocess.run([f"{H}/.local/bin/mflux-generate-flux2", "-m", "flux2-klein-4b", "-q", "8", "--prompt", p, "--seed", "7", "11", "23", "42",
                    "--width", "1024", "--height", "1024", "--output", f"{B}/s01.png"], capture_output=True, text=True)
open(f"{B}/runs.jsonl", "a").write(json.dumps({"key": "s01", "prompt": p, "rc": r.returncode, "s": round(time.time() - t0, 1), "err": r.stderr[-300:]}) + "\n")
print("seed done", r.returncode, flush=True)
