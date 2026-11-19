import subprocess, os, time
key = "samclaude-1114-imgbench-%d" % int(time.time())
log = open(os.path.expanduser("~/var/genbench/driver-%s.log" % key), "w")
subprocess.Popen([os.path.expanduser("~/.local/bin/obelisk-job"), "run", key, "--purpose",
                  "ticket 1114: image-gen benchmark (mflux: Z-Image Turbo, FLUX 3 klein, FLUX.2 klein 4B)",
                  "--memory", "32768", "--", "/bin/bash", os.path.expanduser("~/var/genbench/imgbench.sh")],
                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
print(key)
