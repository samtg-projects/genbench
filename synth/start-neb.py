# Queue two nebula seeds through full-scene.sh, one after the other, detached from the gateway hop.
import subprocess, os
S = os.path.expanduser("~/var/genbench/synth")
env = dict(os.environ, TRANSPARENT="0", BG="0", SUN="0", ELEV="-70,70", DIST="0.6")
cmd = f"{S}/full-scene.sh scene_nebula.py synth-nebula-s0 160 1024 64 0; {S}/full-scene.sh scene_nebula.py synth-nebula-s11 160 1024 64 11"
p = subprocess.Popen(["/bin/bash", "-c", cmd], env=env, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=open(f"{S}/neb-driver.log", "a"), stderr=subprocess.STDOUT)
print("started", p.pid)
