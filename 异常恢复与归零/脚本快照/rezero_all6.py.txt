#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-run the six-axis zero calibration exactly the way it succeeded on
2026-09-24 17:53 (that one was driven from the pendant; this is the same
sequence over HTTP):

    clearAlarms -> enable -> POST /calibrate/home -> wait for
    "servo calihome done ..." -> verify the joints read ~0 -> disable

Notes
  * cali home uses CiA402 homing method 0x6098 = 35 ("current position as
    home") - it does NOT move the arm.
  * it only works while the robot is ENABLED (with the robot disabled the
    drives never report the homing done and the call fails after ~3 s).
  * whatever pose the arm is in when this runs becomes the zero, so make sure
    the arm is on its alignment marks first.
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|robot enabled\\|robot disabled\\|"
        "not collision\\|AlarmSysSetBit\\|isRequestCalihome\\|HomeNumdone\\|"
        "calihome done\\|calihome not done' $L | tail -30\n")


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


def logtail():
    rc, out = szf.ssh_script(GREP, "rezero")
    return out


def main():
    q0 = szf.joint_values()
    print("pose before : %s" % ", ".join("%+.4f" % v for v in q0))
    print("             (this pose becomes the new zero)")

    ok = False
    for attempt in (1, 2, 3):
        print("\n=== enable attempt %d ===" % attempt)
        print("  clearAlarms -> %s" % (post("/interface/clearAlarms"),))
        time.sleep(2.5)
        print("  enable      -> %s"
              % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
        time.sleep(5)
        t = logtail()
        if "not collision" in t.split("=== ")[-1]:
            print("  refused ('exist an error not collision') - retrying")
            time.sleep(3)
            continue
        if "robot enabled" in t:
            ok = True
            break
    if not ok:
        print("\n!! could not enable - aborting")
        return 2

    print("\n=== calibrate ===")
    print("  POST /calibrate/home -> %s" % (post("/calibrate/home"),))
    done = False
    for i in range(15):
        time.sleep(1.5)
        t = logtail()
        if "servo calihome done" in t:
            done = True
            break
        if "HomeNumdone" in t:
            m = re.findall(r"HomeNumdone : (\d+)", t)
            print("   ... HomeNumdone = %s" % (m[-1] if m else "?"))
    print("\n--- log ---")
    for line in t.strip().splitlines()[-14:]:
        print("   " + line.strip())

    q1 = szf.joint_values()
    print("\npose after  : %s" % ", ".join("%+.4f" % v for v in q1))
    print("max |q|     : %.4f deg" % max(abs(v) for v in q1))
    print("calihome    : %s" % ("DONE" if done else "NOT CONFIRMED"))

    print("\ndisable     -> %s"
          % (post("/settings/controlMode", '{"controlMode":"disable"}'),))
    time.sleep(2)
    print("final pose  : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))

    if done and max(abs(v) for v in q1) < 0.5:
        print("\nVERDICT: six-axis zeroing OK - all joints ~0")
        return 0
    print("\nVERDICT: suspicious - check the log above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
