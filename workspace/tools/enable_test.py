#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One controlled enable test after the stock-application rollback.

Prints the pose before, sends clearAlarms + enable, watches the controller log
for 6 s for alarm 0x86 / "robot disabled", then leaves the robot DISABLED again
(so the operator takes over from a known state).
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|robot enabled\\|robot disabled\\|"
        "not collision\\|AlarmSysSetBit\\|enableRobot#40' $L | tail -14\n")


def post(path, body="{}"):
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return str(e)[:60]


def main():
    q0 = szf.joint_values()
    print("pose before : %s" % ", ".join("%+.4f" % v for v in q0))

    print("clearAlarms -> %s" % (post("/interface/clearAlarms"),))
    time.sleep(2)
    print("enable      -> %s"
          % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
    time.sleep(7)
    rc, out = szf.ssh_script(GREP, "test")
    print("--- log ---")
    for line in out.strip().splitlines()[-12:]:
        print("   " + line)

    q1 = szf.joint_values()
    print("\npose after  : %s" % ", ".join("%+.4f" % v for v in q1))
    print("delta       : %s"
          % ", ".join("%+.4f" % (b - a) for a, b in zip(q0, q1)))
    held = "index=0x86" not in out and "robot disabled" not in out
    print("\nVERDICT: %s"
          % ("alarm 0x86 did NOT come back - enable held"
             if held else "still blocked (see log above)"))

    print("disable     -> %s"
          % (post("/settings/controlMode", '{"controlMode":"disable"}'),))
    time.sleep(2)
    print("final pose  : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))
    return 0 if held else 2


if __name__ == "__main__":
    sys.exit(main())
