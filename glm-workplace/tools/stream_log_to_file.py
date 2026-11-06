"""stream_log_to_file.py - run rssh watcher and stream stdout to a utf-8 local file.

Usage: python tools/stream_log_to_file.py <device_script.sh> <local_out.txt>
Killed by stopping the background process (or SSH drop).
"""
import os
import subprocess
import sys

script = sys.argv[1] if len(sys.argv) > 1 else r"sim_scripts\watch_homing_315.sh"
outfile = sys.argv[2] if len(sys.argv) > 2 else r"sim_scripts\homing_watch_live.txt"

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"

with open(outfile, "w", encoding="utf-8", newline="\n") as out:
    p = subprocess.Popen(
        [sys.executable, r"tools\rssh.py", "-f", script],
        stdout=out,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)) + "\\..",
    )
    rc = p.wait()
print("stream ended rc=%s -> %s" % (rc, outfile))
