# Task 1361: TripoSplat one life-cycle series folder (SNN.png) into triposplat/<name>, in one claim.
import subprocess, os, sys, time
H = os.path.expanduser("~"); T = H + "/var/genbench/triposplat"
src, name, n = sys.argv[1], sys.argv[2], sys.argv[3]
key = "samclaude-1361-triposplat-%s-%d" % (name, int(time.time()))
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "task 1361: TripoSplat on the %s series (%s stages)" % (name, n),
                  "--memory", "16384", "--", T + "/venv/bin/python", H + "/var/genbench/tsplat_stream.py", src, T + "/" + name, n, "S[0-9][0-9].png"],
                 stdout=open(T + "/%s-driver.log" % name, "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
