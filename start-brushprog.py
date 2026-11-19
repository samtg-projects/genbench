import subprocess, os, time
H = os.path.expanduser("~")
key = "samclaude-1114-brush-progress-%d" % int(time.time())
out = H + "/var/genbench/wip/brushprog"; os.makedirs(out, exist_ok=True)
log = open(H + "/var/genbench/wip/brushprog-driver.log", "w")
subprocess.Popen([H + "/.local/bin/obelisk-job", "run", key, "--purpose", "ticket 1114 / doc 660: Brush training-progress video (Gazania v2, export every 1000 steps)",
                  "--memory", "20480", "--", "/bin/sh", "-c",
                  "t0=$(date +%s); " + H + "/.local/bin/brush_app " + H + "/workcloud/data/nerfstudio/synth-gazania-v2/dataset --total-steps 30000 --export-every 1000 --export-path " + out + " > " + out + "/brush.log 2>&1; echo train_s=$(( $(date +%s) - t0 ))"],
                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
