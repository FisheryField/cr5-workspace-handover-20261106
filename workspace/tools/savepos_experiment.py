#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Experiment: does the PLC compare the live joint pose with
/home/ftp/PlcLogic/Recipe/SavePos.txt when the robot is enabled?

Background: mToolServer writes SavePos.txt (6 float64 joint values + trailer)
right before it starts a servo FoE flash, and writes "777" into Update.txt.
alarm 0x86 = "上使能关节位置偏差过大" fires ~0.3 s after every successful
enable, and the PLC application binary contains the SavePos.txt path twice,
so the alarm is plausibly the PLC noticing that the pose recorded before the
flash no longer matches reality (the servos lost their zero).

This script backs up SavePos.txt, rewrites the six float64 values with the
joint values that are reported right now, then clears alarms + enables and
reports whether alarm 0x86 comes back.
"""
import json
import os
import struct
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

REMOTE = "/home/ftp/PlcLogic/Recipe/SavePos.txt"
LOCAL = os.path.join(szf.ROOT, "data", "SavePos_new.txt")

GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|not collision\\|AlarmSysSetBit\\|"
        "isRequestCalihome\\|HomeNumdone\\|calihome done\\|robot enabled\\|"
        "robot disabled\\|SavePos' $L | tail -25\n")


def post(path, body="{}"):
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")[:160]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:160]


def tail(label):
    rc, out = szf.ssh_script(GREP, "seq")
    print("--- %s" % label)
    for line in out.strip().splitlines()[-10:]:
        print("    " + line)


def main():
    rc, out = szf.ssh_script(
        "cp -a %s %s.bak_%s; ls -la %s*; echo '--- original (od)'; "
        "od -An -tx1 %s\n"
        % (REMOTE, REMOTE, time.strftime("%Y%m%d_%H%M%S"), REMOTE, REMOTE),
        "bak")
    print(out.strip())

    q = szf.joint_values()
    print("\nlive joint values : %s" % json.dumps(q))

    # keep everything after the 48 bytes of float64 payload untouched
    rc = szf.scp_get(REMOTE, LOCAL)
    print("pull rc=%d" % rc[0])
    blob = bytearray(open(LOCAL, "rb").read())
    if len(blob) < 48:
        raise SystemExit("!! SavePos.txt too short (%d bytes)" % len(blob))
    struct.pack_into("<6d", blob, 0, *q)
    open(LOCAL, "wb").write(bytes(blob))
    print("new payload : %s" % (struct.unpack_from("<6d", bytes(blob), 0),))
    print("trailer kept: %s" % bytes(blob[48:]).hex(" "))

    rc = szf.scp_put(LOCAL, REMOTE)
    print("upload rc=%d" % rc[0])
    rc, out = szf.ssh_script("od -An -tx1 %s\n" % REMOTE, "chk")
    print("on controller: %s" % out.strip())

    print("\nPOST /interface/clearAlarms -> %s" % (post("/interface/clearAlarms"),))
    time.sleep(3)
    print("POST /settings/controlMode enable -> %s"
          % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
    time.sleep(8)
    tail("after enable")
    print("\njoints after : %s" % json.dumps(szf.joint_values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
