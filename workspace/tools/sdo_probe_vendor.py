#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic read-only SDO probe through codesyscontrol's HTTP route.

The value is not in the HTTP reply: it shows up in the controller log as
    [readSDO#4624] sdo read fail,slave=N,index=<DEC>,subIndex=S,value=V.
("sdo read fail" is a vendor wording bug printed on the success path; the
readback is truncated to the low 16 bits for 32-bit objects.)
One request at a time; the controller needs ~1 s between requests.
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

# vendor H-group objects, per official servoCSV/param.csv: H<group>.<n> == 0x20<group>:<n+1>
TARGETS = [
    (0x5000, 7),    # POSITIVE CONTROL: firmware version word (must read 12624 on 3.1.5.0)
    (0x2000, 1),    # H00.00
    (0x2001, 18),   # H01.17 编码器位置角
    (0x2001, 19),   # H01.18 编码器校零电流
    (0x200C, 1),    # H0C.00 故障复位
    (0x200C, 3),    # H0C.02 编码器校零使能
    (0x6064, 0),    # reference: position actual value
    (0x6062, 0),    # reference: position demand value
]


def hit(servo, index, sub):
    body = json.dumps({"body": [{"key": "addr%04X%02X" % (index, sub),
                                 "servoNum": servo, "value": 0}]}).encode()
    req = urllib.request.Request(
        "http://%s:22000/settings/readServoParams" % szf.CTRL_IP, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return "ERR %s" % str(e)[:60]


def main():
    axes = sys.argv[1:] or ["J1", "J6"]
    for servo in axes:
        for index, sub in TARGETS:
            st = hit(servo, index, sub)
            print("  %-3s 0x%04X:%02d -> %s" % (servo, index, sub, st))
            sys.stdout.flush()
            time.sleep(1.15)
    print("\n--- results from the controller log ---")
    for slave, index, sub, val in sorted(szf.read_log_tail()):
        if (index, sub) in TARGETS:
            print("  slave %d / %-3s 0x%04X:%02d = %d"
                  % (slave, szf.AXIS_OF_SLAVE.get(slave, "?"), index, sub, val))
    return 0


if __name__ == "__main__":
    sys.exit(main())
