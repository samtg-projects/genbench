import subprocess, os, time
H = os.path.expanduser("~")
key = "samclaude-1114-triposplat-life25-%d" % int(time.time())
log = open(H + "/var/genbench/tsplat-life25-driver.log", "w")
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "ticket 1114: TripoSplat on claude-wafer's 25-stage white-rose life cycle (life25)",
                  "--memory", "16384", "--", H + "/var/genbench/triposplat/venv/bin/python", H + "/var/genbench/tsplat_stream.py",
                  H + "/var/claude-wafer-1353/life25", H + "/var/genbench/triposplat/life25", "25", "L[0-9][0-9].png"],
                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
