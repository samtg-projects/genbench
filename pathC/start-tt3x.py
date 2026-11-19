# Task 1357: the joined 15 s turntable (turntable + cont + cont2) through pathC-splat.sh at 4 fps, detached.
import subprocess, os
O = os.path.expanduser("~/var/genbench/pathC")
p = subprocess.Popen(["/bin/bash", os.path.expanduser("~/var/genbench/pathC-splat.sh"), "pathC-turntable-3x", f"{O}/turntable-3x.mp4", "4"], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=open(f"{O}/tt3x-driver.log", "a"), stderr=subprocess.STDOUT)
print("started", p.pid)
