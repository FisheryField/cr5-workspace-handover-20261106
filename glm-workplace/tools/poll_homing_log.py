"""poll_homing_log.py - device-side incremental probe + local append, run as a loop.

Each cycle: runs sim_scripts/homing_probe.sh on the device via tools/rssh.py -f,
appends any new homing-relevant lines to the local watch file. The device keeps
its cursor in /tmp so each cycle only transfers new lines. Exits when told to
stop (file sim_scripts/STOP_HOMING_POLL exists) or on repeated SSH failures.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
RSSH = os.path.join("tools", "rssh.py")
PROBE = os.path.join("sim_scripts", "homing_probe.sh")
OUT = os.path.join("sim_scripts", "homing_watch_live.txt")
STOP = os.path.join("sim_scripts", "STOP_HOMING_POLL")


def main() -> int:
    interval = 10
    fails = 0
    with open(OUT, "a", encoding="utf-8", newline="\n") as out:
        out.write("[poll] start %s\n" % time.strftime("%H:%M:%S"))
        out.flush()
        while not os.path.exists(STOP):
            p = subprocess.run(
                [sys.executable, RSSH, "-f", PROBE],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", cwd=ROOT, timeout=90,
            )
            if p.returncode == 0:
                fails = 0
                if p.stdout.strip():
                    out.write(p.stdout if p.stdout.endswith("\n") else p.stdout + "\n")
                    out.flush()
            else:
                fails += 1
                out.write("[poll] ssh fail #%d rc=%s\n" % (fails, p.returncode))
                out.flush()
                if fails >= 6:
                    out.write("[poll] giving up after 6 consecutive failures\n")
                    break
            time.sleep(interval)
        out.write("[poll] stop %s\n" % time.strftime("%H:%M:%S"))
        out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
