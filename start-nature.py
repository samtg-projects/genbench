# Task 1361: TripoSplat claude-wafer's 12 nature picks, then the 12 alternate seeds, in one claim.
import subprocess, os, time
H = os.path.expanduser("~"); T = H + "/var/genbench/triposplat"; N = H + "/var/claude-wafer-1353/nature"
for d in ("nature-in/picks", "nature-in/alts", "nature", "nature-alt"): os.makedirs(f"{T}/{d}", exist_ok=True)
for line in open(N + "/picks.txt"):
    rel = line.strip()
    if not rel: continue
    subj = rel.split("/")[0]; seed = rel.rsplit("_seed_", 1)[1][0]; alt = "2" if seed == "1" else "1"
    for src, dst in ((f"{N}/{rel}", f"{T}/nature-in/picks/{subj}.png"), (f"{N}/{subj}/{subj}_seed_{alt}.png", f"{T}/nature-in/alts/{subj}.png")):
        if os.path.exists(src) and not os.path.exists(dst): os.link(src, dst)
py, st = T + "/venv/bin/python", H + "/var/genbench/tsplat_stream.py"
cmd = f"{py} {st} {T}/nature-in/picks {T}/nature 12 '*.png' && {py} {st} {T}/nature-in/alts {T}/nature-alt 12 '*.png'"
key = "samclaude-1361-triposplat-nature-%d" % int(time.time())
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "task 1361: TripoSplat on 12 nature picks, then the 12 alternate seeds",
                  "--memory", "16384", "--", "/bin/sh", "-c", cmd],
                 stdout=open(T + "/nature-driver.log", "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key, len(os.listdir(T + "/nature-in/picks")), len(os.listdir(T + "/nature-in/alts")))
