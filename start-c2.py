import subprocess, os, time
H = os.path.expanduser("~")
key = "samclaude-1357-video2-%d" % int(time.time())
log = open(H + "/var/genbench/pathC/driver2.log", "w")
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "task 1357 pathway C: Wan 2.2 TI2V-5B turntable continuation x2 + second seed (3 x 121 frames, 704^2), exclusive",
                  "--exclusive", "--", "/bin/bash", H + "/var/genbench/c-video2.sh"],
                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
