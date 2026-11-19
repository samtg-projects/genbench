import subprocess, os, time
H = os.path.expanduser("~"); T = H + "/var/genbench/triposplat"
os.makedirs(T + "/life28", exist_ok=True)
# Carry the unchanged 25 over: life25 L01-L22 keep their names, old L23-L25 become L26-L28.
for i in range(1, 26):
    j = i if i <= 22 else i + 3
    for suf in (".ply", "-prepared.webp"):
        src, dst = "%s/life25/L%02d%s" % (T, i, suf), "%s/life28/L%02d%s" % (T, j, suf)
        if not os.path.exists(dst): os.link(src, dst)
key = "samclaude-1114-triposplat-life28-%d" % int(time.time())
log = open(T + "/life28-driver.log", "w")
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "ticket 1114: TripoSplat on life28 L23-L25 (the L22->L23 bridge stages)",
                  "--memory", "16384", "--", T + "/venv/bin/python", H + "/var/genbench/tsplat_stream.py",
                  H + "/var/claude-wafer-1353/life28", T + "/life28", "28", "L[0-9][0-9].png"],
                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
