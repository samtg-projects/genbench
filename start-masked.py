# Task 1361: one claim for the masked fungi run.
import subprocess, os, time
H = os.path.expanduser("~"); T = H + "/var/genbench/triposplat"
key = "samclaude-1361-triposplat-fungi-masked-%d" % int(time.time())
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "task 1361: TripoSplat fungi with mound-preserving mattes (8 stages)",
                  "--memory", "16384", "--", T + "/venv/bin/python", H + "/var/genbench/tsplat_masked.py", H + "/var/claude-wafer-1353/nature/fungi-final",
                  T + "/fungi-masked", "S01.png", "S02,S03,S04,S05,S06,S07"] + ["S%02d.png" % i for i in range(1, 9)],
                 stdout=open(T + "/fungi-masked-driver.log", "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
