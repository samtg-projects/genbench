import subprocess, os
p = os.path.expanduser("~/var/genbench/pathC/posesweep/brushdiag.sh")
subprocess.Popen(["/bin/bash", p], start_new_session=True, stdin=subprocess.DEVNULL, stdout=open(p + ".log", "w"), stderr=subprocess.STDOUT)
