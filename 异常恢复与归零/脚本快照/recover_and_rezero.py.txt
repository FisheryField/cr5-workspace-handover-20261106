#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recover + re-zero the six axes.

Order (each step verified from FRESH log lines only, via a line-count marker):
  1. read the drives' CiA402 state; any axis with 0x603F != 0 is faulted and
     MUST be reset first - the controller refuses to enable while one is
     faulted ("exist an error not collision, can't enable robot"), and a
     cali home attempted in that state stalls at HomeNumdone < 6.
  2. vendor fault reset: write H0C.00 (= 0x200C:01, "故障复位") = 1.  This is
     the same route the vendor tool uses (servoParams.json on 9/23 contains
     exactly {"key":"addr200C01","servoNum":"J6","value":0}).
  3. clearAlarms -> enable -> confirm "robot enabled" with no 0x86.
  4. POST /calibrate/home -> wait for "servo calihome done ...".
  5. verify the six joints read ~0, then disable.
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

L = "/dobot/userdata/CR5_sys_files/project/logs/all/log"
FRESH = ("tail -n +%d %s | grep -a 'settControlMode : \\|robot enabled\\|"
         "robot disabled\\|AlarmSysSetBit\\|isRequestCalihome\\|HomeNumdone\\|"
         "calihome done\\|calihome not done\\|not collision\\|g_isErr'\n")


def ssh(cmd, label="x"):
    return szf.ssh_script(cmd, label)[1]


def marker():
    out = ssh("wc -l < %s\n" % L, "mark")
    m = re.search(r"(\d+)", out)
    return int(m.group(1)) if m else 0


def fresh(since):
    return ssh(FRESH % (since + 1, L), "fresh")


def post(path, body="{}"):
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")[:120]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:120]


def sdo_state(servo):
    """(statusword, errorcode) for one axis, from fresh SDO reads."""
    m = marker()
    for index in (0x6041, 0x603F):
        post("/settings/readServoParams",
             json.dumps({"body": [{"key": "addr%04X00" % index,
                                   "servoNum": servo, "value": 0}]}))
        time.sleep(1.15)
    out = fresh(m)
    sw = ec = None
    for line in out.splitlines():
        mm = re.search(r"slave=(\d+),index=(\d+),subIndex=0,value=(-?\d+)", line)
        if not mm:
            continue
        if int(mm.group(2)) == 0x6041:
            sw = int(mm.group(3))
        if int(mm.group(2)) == 0x603F:
            ec = int(mm.group(3))
    return sw, ec


def reset_fault(servo):
    return post("/settings/modifyServoParams", json.dumps(
        {"body": [{"key": "addr200C01", "servoNum": servo, "value": 1}]}))


def main():
    axes = [szf.AXIS_OF_SLAVE[s] for s in sorted(szf.AXIS_OF_SLAVE)]
    print("pose before : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))

    print("\n=== 1) drive state + fault reset ===")
    for servo in axes:
        sw, ec = sdo_state(servo)
        tag = "OK" if ec == 0 else "FAULT"
        print("   %-3s statusword=0x%04X errorcode=0x%04X  %s"
              % (servo, sw or 0, ec or 0, tag))
        if ec:
            print("        -> H0C.00 fault reset = %s" % (reset_fault(servo),))
            time.sleep(1.5)
            sw, ec = sdo_state(servo)
            print("        -> now statusword=0x%04X errorcode=0x%04X  %s"
                  % (sw or 0, ec or 0, "OK" if ec == 0 else "STILL FAULTED"))

    print("\n=== 2) clear alarms + enable ===")
    ok = False
    for attempt in (1, 2, 3):
        m = marker()
        print("   attempt %d: clearAlarms=%s" % (attempt, post("/interface/clearAlarms"),))
        time.sleep(2.5)
        m = marker()
        print("              enable=%s"
              % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
        time.sleep(6)
        t = fresh(m)
        if "not collision" in t:
            print("              refused - retrying")
            time.sleep(3)
            continue
        if "robot enabled" in t:
            ok = True
            print("              enabled OK")
            break
    if not ok:
        print("\n!! cannot enable - aborting")
        return 2

    m = marker()
    t = fresh(m)
    if "index=0x86" in t:
        print("\n!! alarm 0x86 fired right after enable - aborting")
        post("/settings/controlMode", '{"controlMode":"disable"}')
        return 3

    print("\n=== 3) calibrate ===")
    m = marker()
    print("   POST /calibrate/home -> %s" % (post("/calibrate/home"),))
    done = False
    for _ in range(20):
        time.sleep(1.5)
        t = fresh(m)
        if "servo calihome done" in t:
            done = True
            break
    for line in t.strip().splitlines()[-12:]:
        print("   " + line.strip())

    q = szf.joint_values()
    print("\npose after  : %s" % ", ".join("%+.4f" % v for v in q))
    print("max |q|     : %.4f deg     calihome: %s"
          % (max(abs(v) for v in q), "DONE" if done else "NOT CONFIRMED"))

    print("\ndisable     -> %s" % (post("/settings/controlMode", '{"controlMode":"disable"}'),))
    time.sleep(2.5)
    print("final pose  : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))
    print("\nVERDICT: %s"
          % ("six-axis zeroing OK - all joints ~0"
             if done and max(abs(v) for v in q) < 0.5 else "see the log above"))
    return 0 if (done and max(abs(v) for v in q) < 0.5) else 1


if __name__ == "__main__":
    sys.exit(main())
