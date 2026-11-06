#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try the /settings/controlMode payload shapes until the controller reports
    settControlMode : enable
then run POST /calibrate/home and report the joint values.

The JSON key is literally "controlMode" (string table of libdataSvr.so:
"...| controlMode | settControlMode : {} | enable | ..."); only the envelope
shape is unknown, so a few are tried and each attempt is verified in the
controller log (read-only).
"""
import io
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

CANDIDATES = [
    '{"controlMode":"enable"}',
    '{"body":[{"key":"controlMode","value":"enable"}]}',
    '{"body":{"controlMode":"enable"}}',
    '{"body":"enable"}',
    '{"key":"controlMode","value":"enable"}',
    '{"body":[{"controlMode":"enable"}]}',
    '{"controlMode":1}',
]


def post(path, body):
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def log_tail_since(marker):
    rc, out = szf.ssh_script(
        "L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|robot enabled\\|robot disabled\\|"
        "AlarmSysSetBit\\|isRequestCalihome\\|HomeNumdone\\|calihome' $L | tail -25\n",
        "cmode")
    return out


def main():
    print("before: %s" % json.dumps(szf.joint_values()))
    ok = False
    for cand in CANDIDATES:
        print("\n--- POST /settings/controlMode  %s" % cand)
        print("    -> %s" % (post("/settings/controlMode", cand),))
        time.sleep(3.5)
        tail = log_tail_since("")
        print("    log tail:\n%s" % "\n".join("      " + l for l in
                                              tail.strip().splitlines()[-8:]))
        if "settControlMode : enable" in tail:
            ok = True
            print("    ==> control mode accepted")
            break
    if not ok:
        print("\n!! no candidate was accepted - stopping")
        return 2

    time.sleep(4)
    print("\n--- POST /calibrate/home")
    print("    -> %s" % (post("/calibrate/home", "{}"),))
    time.sleep(6)
    print("\n--- log after calibration:")
    print("\n".join("      " + l for l in
                    log_tail_since("").strip().splitlines()[-14:]))
    print("\nafter : %s" % json.dumps(szf.joint_values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
