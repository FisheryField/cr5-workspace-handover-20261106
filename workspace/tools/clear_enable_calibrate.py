#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clear alarms -> enable -> zero calibration, with log verification.

Route map (from dobotlink/IndustrialRobotPlugin.dll, dobot's own client):
    ClearAlarms2   -> /interface/clearAlarms
    SetControlMode -> /settings/controlMode
The enable is refused ("exist an error not collision, can't enable robot")
while a controller alarm is latched, so the alarm must be cleared first.
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|can not enable\\|can't enable\\|"
        "AlarmSysSetBit\\|isRequestCalihome\\|HomeNumdone\\|calihome done\\|"
        "clearError\\|clearAlarm\\|robot enabled\\|robot disabled' $L | tail -30\n")


def post(path, body="{}"):
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def tail(label):
    rc, out = szf.ssh_script(GREP, "seq")
    print("--- %s" % label)
    for line in out.strip().splitlines()[-12:]:
        print("    " + line)


def main():
    print("joints before : %s" % json.dumps(szf.joint_values()))

    print("\n1) POST /interface/clearAlarms  -> %s"
          % (post("/interface/clearAlarms"),))
    time.sleep(3)
    tail("after clearAlarms")

    print("\n2) POST /settings/controlMode enable -> %s"
          % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
    time.sleep(6)
    tail("after enable")

    print("\n3) POST /calibrate/home -> %s" % (post("/calibrate/home"),))
    time.sleep(7)
    tail("after calibrate")

    print("\njoints after  : %s" % json.dumps(szf.joint_values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
