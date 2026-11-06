#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test whether the drive's CiA402 home offset 0x607C can shift the reported
position actual value 0x6064 (read-only objects can't, writable ones can).

Why it matters: on this servo firmware the "position demand value" 0x6062
becomes the raw absolute encoder count while the axis is enabled, whereas
0x6064 stays re-based.  The controller raises alarm 0x86 whenever
|0x6062 - 0x6064| exceeds a threshold, which is what blocks enabling now that
the zero bases are garbage (57..139 deg).  If 0x607C shifts 0x6064 only, it is
a writable lever that can make the difference small enough to enable, and a
calibration can then be run.

Everything here is read/modify-back on one axis: 0x607C is restored to
whatever it was.
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

TEST = 100000


def req(path, body):
    r = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                               data=body.encode(),
                               headers={"Content-Type": "application/json"},
                               method="POST")
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")[:120]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:120]


def rd(servo, index, sub=0):
    return req("/settings/readServoParams", json.dumps(
        {"body": [{"key": "addr%04X%02X" % (index, sub),
                   "servoNum": servo, "value": 0}]}))


def wr(servo, index, sub, value):
    return req("/settings/modifyServoParams", json.dumps(
        {"body": [{"key": "addr%04X%02X" % (index, sub),
                   "servoNum": servo, "value": value}]}))


def latest(servo, index, sub=0):
    for slave, i, s, v in sorted(szf.read_log_tail()):
        if i == index and s == sub:
            return slave, v
    return None, None


def main():
    servo = sys.argv[1] if len(sys.argv) > 1 else "J1"
    val = int(sys.argv[2]) if len(sys.argv) > 2 else TEST

    print("1) read 0x607C (baseline)"); print("   %s" % (rd(servo, 0x607C),))
    time.sleep(1.2)
    print("2) read 0x6064 (before)"); print("   %s" % (rd(servo, 0x6064),))
    time.sleep(1.2)
    print("   -> controller log: %s" % (szf.read_log_tail(),))
    print()
    print("3) WRITE 0x607C = %d" % val); print("   %s" % (wr(servo, 0x607C, 0, val),))
    time.sleep(1.2)
    print("4) read 0x607C back"); print("   %s" % (rd(servo, 0x607C),))
    time.sleep(1.2)
    print("5) read 0x6064 (after)"); print("   %s" % (rd(servo, 0x6064),))
    time.sleep(1.2)
    print("6) restore 0x607C = 0"); print("   %s" % (wr(servo, 0x607C, 0, 0),))
    time.sleep(1.2)
    print("7) read 0x6064 (restored)"); print("   %s" % (rd(servo, 0x6064),))
    time.sleep(1.2)
    print("\n--- controller log values ---")
    for slave, index, sub, v in sorted(szf.read_log_tail()):
        if index in (0x607C, 0x6064):
            print("  slave %d 0x%04X:%02d = %d" % (slave, index, sub, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
