#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the CiA402 state of all six drives (statusword / error code / mode /
homing method) through codesyscontrol's read-only SDO route."""

import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

TARGETS = [(0x6041, "statusword"), (0x603F, "error code"),
           (0x6060, "mode"), (0x6061, "mode display"), (0x6098, "homing method"),
           (0x6064, "position actual (low16)")]

BITS = [("ready to switch on", 0), ("switched on", 1), ("op enabled", 2),
        ("FAULT", 3), ("voltage enabled", 4), ("quick stop", 5),
        ("switch on disabled", 6), ("warning", 7), ("remote", 9),
        ("target reached", 10), ("internal limit", 11)]


def hit(servo, index, sub=0):
    body = json.dumps({"body": [{"key": "addr%04X%02X" % (index, sub),
                                 "servoNum": servo, "value": 0}]}).encode()
    req = urllib.request.Request(
        "http://%s:22000/settings/readServoParams" % szf.CTRL_IP, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20):
            return True
    except Exception:  # noqa: BLE001
        return False


def main():
    for slave, name in szf.AXIS_OF_SLAVE.items():
        for index, _ in TARGETS:
            hit(name, index)
            time.sleep(1.1)

    got = {}
    for slave, index, sub, val in szf.read_log_tail():
        if index in dict(TARGETS):
            got.setdefault(slave, {})[index] = val

    for slave in sorted(szf.AXIS_OF_SLAVE):
        name = szf.AXIS_OF_SLAVE[slave]
        d = got.get(slave, {})
        sw = d.get(0x6041)
        print("=== slave %d / %s ===" % (slave, name))
        for index, label in TARGETS:
            print("   0x%04X %-24s = %s"
                  % (index, label,
                     d.get(index, "<no data>")))
        if sw is not None:
            flags = [lbl for lbl, b in BITS if (sw >> b) & 1]
            print("   statusword bits: %s" % ", ".join(flags))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
