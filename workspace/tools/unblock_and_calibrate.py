#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clear alarms -> enable -> wait -> zero calibration (/calibrate/home).

Steps are verified in the controller log:
  * "exist an error not collision, can't enable robot"  -> enable was refused
    (a controller alarm is latched); retry after /interface/clearAlarms
  * "robot enabled"                                     -> enable accepted
  * "HomeNumdone : N"                                   -> how many axes have
    reported the homing done; a successful calibration prints "servo calihome
    done ..." after HomeNumdone reaches the axis count
  * "AlarmSysSetBit() index=0x86"                       -> the deviation alarm
    fired and the controller will drop back to disabled
"""
import json
import os
import struct
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|not collision\\|AlarmSysSetBit\\|"
        "isRequestCalihome\\|HomeNumdone\\|calihome done\\|calihome not\\|"
        "robot enabled\\|robot disabled\\|monitorErrorStatus' $L | tail -24\n")

SAVEPOS = "/home/ftp/PlcLogic/Recipe/SavePos.txt"


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


def tail(label, n=12):
    rc, out = szf.ssh_script(GREP, "seq")
    lines = out.strip().splitlines()[-n:]
    print("--- %s" % label)
    for line in lines:
        print("    " + line)
    return "\n".join(lines)


def enable_once():
    print("  POST /interface/clearAlarms -> %s" % (post("/interface/clearAlarms"),))
    time.sleep(2.5)
    print("  POST /settings/controlMode enable -> %s"
          % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
    time.sleep(5)
    return tail("after enable attempt")


def main():
    print("joints before : %s" % json.dumps(szf.joint_values()))

    ok = False
    for attempt in (1, 2, 3):
        print("\n=== attempt %d ===" % attempt)
        t = enable_once()
        if "robot enabled" in t or "settControlMode setup enable" in t:
            ok = True
            break
        if "not collision" in t:
            print("  -> still refused; waiting 5 s and retrying")
            time.sleep(5)
    if not ok:
        print("\n!! the controller keeps refusing to enable")
        return 2

    print("\n=== calibration ===")
    print("  POST /calibrate/home -> %s" % (post("/calibrate/home"),))
    time.sleep(10)
    tail("after calibration", 18)

    q = szf.joint_values()
    print("\njoints after  : %s" % json.dumps(q))
    print("degrees       : %s" % ", ".join("%+.4f" % v for v in q))

    # keep the vendor's pose record in step with reality
    local = os.path.join(szf.ROOT, "data", "SavePos_new.txt")
    szf.scp_get(SAVEPOS, local)
    blob = bytearray(open(local, "rb").read())
    struct.pack_into("<6d", blob, 0, *q)
    open(local, "wb").write(bytes(blob))
    print("rewrote SavePos.txt payload -> %s" % (szf.scp_put(local, SAVEPOS)[0],))
    return 0


if __name__ == "__main__":
    sys.exit(main())
