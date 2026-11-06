#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only SDO probe via codesyscontrol HTTP (port 22000).

One request at a time (concurrent requests -> HTTP 400).
The value is NOT in the HTTP reply: it appears in the controller log as
    [readSDO#4624] sdo read fail,slave=N,index=<DEC>,subIndex=0,value=V.
("sdo read fail" is a vendor wording bug printed on the success path.)
NOTE: SDO readback returns only the LOW 16 BITS of a 32-bit object.
"""
import json
import sys
import time
import urllib.request

BASE = "http://192.168.5.1:22000/settings/readServoParams"

# (servoNum, index-hex) -> we always use subindex 00
TARGETS = []
for ax in range(1, 7):
    for idx in ("607C", "6041", "603F", "6098"):
        TARGETS.append(("J%d" % ax, idx))


def hit(servo, idx, timeout=20):
    body = json.dumps({"body": [{"key": "addr%s00" % idx,
                                 "servoNum": servo,
                                 "value": 0}]}).encode()
    req = urllib.request.Request(BASE, data=body,
                                headers={"Content-Type": "application/json"},
                                method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def main():
    ok = 0
    for servo, idx in TARGETS:
        st, txt = hit(servo, idx)
        print("%-3s %s -> %s %s" % (servo, idx, st, txt))
        sys.stdout.flush()
        if st == 200:
            ok += 1
        time.sleep(1.2)
    print("posted %d/%d" % (ok, len(TARGETS)))


if __name__ == "__main__":
    main()
