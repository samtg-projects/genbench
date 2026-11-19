import subprocess, os, time
H = os.path.expanduser("~")
key = "samclaude-1357-orbit-video-%d" % int(time.time())
os.makedirs(H + "/var/genbench/pathC", exist_ok=True)
log = open(H + "/var/genbench/pathC/driver.log", "w")
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "task 1357 pathway C: Wan 2.2 TI2V-5B orbit and turntable videos (2 x 121 frames, 704^2)",
                  "--memory", "98304", "--", "/bin/bash", H + "/var/genbench/c-video.sh"],
                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
