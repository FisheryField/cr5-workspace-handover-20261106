#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reset a drive fault via the known-good HTTP SDO write channel.

POST :22000/settings/modifyServoParams
body {"body":[{"key":"addr<idx4hex><sub2hex>","servoNum":"J1".."J6","value":n}]}
Writes CiA402 controlword 0x6040 = 0x80 (fault reset, bit 7) -- the standard
DS402 way to clear a latched drive alarm. One request at a time per channel rule.

usage: python tools/sdo_fault_reset.py J1 [J2 ...]
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402


def post(body):
    req = urllib.request.Request(
        "http://%s:22000/settings/modifyServoParams" % szf.CTRL_IP,
        data=body.encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def main():
    axes = [a.upper() for a in sys.argv[1:]] or ["J1"]
    for a in axes:
        body = json.dumps({"body": [{"key": "addr604000",
                                    "servoNum": a,
                                    "value": 128}]})
        print("POST modifyServoParams %s  0x6040=0x80  body=%s" % (a, body))
        print("   -> %s" % (post(body),))
        time.sleep(2)
    rc, out = szf.ssh_script(
        "L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'logServoError\\|AlarmSysSetBit\\|lastAlarmHappened:"
        "false\\|robot enabled\\|robot disabled' $L | tail -12\n", "fr")
    print("--- log tail")
    for line in out.strip().splitlines()[-12:]:
        print("    " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
