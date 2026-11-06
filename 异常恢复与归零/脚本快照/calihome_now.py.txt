#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run POST /calibrate/home right now (the robot is already enabled) and verify.

Log freshness is handled with a line-count marker, so stale lines from earlier
sessions can never be mistaken for fresh ones.
"""
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

L = "/dobot/userdata/CR5_sys_files/project/logs/all/log"
MARK = "wc -l < %s\n" % L
TAIL = ("tail -n +%d %s | grep -a 'settControlMode : \\|robot enabled\\|"
        "robot disabled\\|AlarmSysSetBit\\|isRequestCalihome\\|HomeNumdone\\|"
        "calihome done\\|calihome not done\\|monitorErrorStatus'\n")


def ssh(cmd, label="x"):
    rc, out = szf.ssh_script(cmd, label)
    return out


def marker():
    out = ssh(MARK, "mark")
    m = re.search(r"^\s*(\d+)\s*$", out, re.M)
    return int(m.group(1)) if m else 0


def fresh(since):
    return ssh(TAIL % (since + 1, L), "fresh")


def post(path, body="{}"):
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")[:120]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:120]


def main():
    q0 = szf.joint_values()
    print("pose before : %s" % ", ".join("%+.4f" % v for v in q0))

    n0 = marker()
    recent = fresh(n0 - 60)
    enabled = "robot enabled" in recent and "robot disabled" not in recent.split("robot enabled")[-1][:400]
    print("robot state : %s" % ("ENABLED" if enabled else "not enabled?"))

    m = marker()
    print("\nPOST /calibrate/home -> %s" % (post("/calibrate/home"),))
    done = False
    last = ""
    for _ in range(16):
        time.sleep(1.5)
        last = fresh(m)
        if "servo calihome done" in last:
            done = True
            break
        if "calihome not done" not in last and "HomeNumdone" not in last and last.strip():
            pass
    print("\n--- fresh log lines ---")
    for line in last.strip().splitlines()[-16:]:
        print("   " + line.strip())

    q1 = szf.joint_values()
    print("\npose after  : %s" % ", ".join("%+.4f" % v for v in q1))
    print("max |q|     : %.4f deg" % max(abs(v) for v in q1))
    print("calihome    : %s" % ("DONE" if done else "NOT CONFIRMED"))

    print("\ndisable     -> %s"
          % (post("/settings/controlMode", '{"controlMode":"disable"}'),))
    time.sleep(2.5)
    print("final pose  : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))
    print("\nVERDICT: %s"
          % ("six-axis zeroing OK - all joints ~0"
             if done and max(abs(v) for v in q1) < 0.5 else "check the log above"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
