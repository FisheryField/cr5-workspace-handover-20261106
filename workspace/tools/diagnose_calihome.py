#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enable the robot, dump every drive's CiA402 state WHILE ENABLED, then run
cali home and report which axes do and do not complete the homing.

Freshness of log lines is handled with a line-count marker, and the SDO lines
(readSDO#...) are explicitly included in the grep (missing them was a bug in
the previous script).
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
         "calihome done\\|calihome not done\\|not collision\\|g_isErr\\|"
         "readSDO#46\\|sdo write'\n")

SW_BITS = [("ready", 0), ("switched on", 1), ("OP-ENABLED", 2), ("FAULT", 3),
           ("volt", 4), ("qstop", 5), ("switch-on-dis", 6), ("warn", 7),
           ("remote", 9), ("tgt-reached", 10), ("int-limit", 11)]


def ssh(cmd, label="x"):
    return szf.ssh_script(cmd, label)[1]


def marker():
    m = re.search(r"(\d+)", ssh("wc -l < %s\n" % L, "mark"))
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
            return r.status
    except Exception as e:  # noqa: BLE001
        return str(e)[:60]


def read_axis_state():
    """-> {slave: {'sw':..,'ec':..,'mode':..,'pos':..}} from fresh log lines."""
    axes = sorted(szf.AXIS_OF_SLAVE)
    m = marker()
    for slave in axes:
        for index in (0x6041, 0x603F, 0x6061, 0x6064):
            post("/settings/readServoParams", json.dumps(
                {"body": [{"key": "addr%04X00" % index,
                           "servoNum": szf.AXIS_OF_SLAVE[slave], "value": 0}]}))
            time.sleep(1.15)
    res = {}
    for line in fresh(m).splitlines():
        mm = re.search(r"slave=(\d+),index=(\d+),subIndex=0,value=(-?\d+)", line)
        if not mm:
            continue
        res.setdefault(int(mm.group(1)), {})[int(mm.group(2))] = int(mm.group(3))
    return res


def show(res):
    for slave in sorted(szf.AXIS_OF_SLAVE):
        d = res.get(slave, {})
        sw = d.get(0x6041)
        print("   %-3s sw=0x%04X ec=0x%04X mode=%s   %s"
              % (szf.AXIS_OF_SLAVE[slave], sw if sw is not None else 0,
                 d.get(0x603F, -1) if d.get(0x603F) is not None else -1,
                 d.get(0x6061, "?"),
                 ", ".join(lbl for lbl, b in SW_BITS if sw is not None and (sw >> b) & 1)))


def main():
    print("pose before : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))

    ok = False
    for attempt in (1, 2, 3, 4):
        m = marker()
        print("\n=== enable attempt %d ===" % attempt)
        post("/interface/clearAlarms")
        time.sleep(2.5)
        m = marker()
        post("/settings/controlMode", '{"controlMode":"enable"}')
        time.sleep(6)
        t = fresh(m)
        if "not collision" in t:
            print("   refused - retrying")
            time.sleep(3)
            continue
        if "robot enabled" in t:
            ok = True
            print("   robot enabled")
            break
    if not ok:
        print("!! cannot enable")
        return 2

    m = marker()
    t = fresh(m)
    print("   fresh warnings right after enable: %s"
          % ("0x86 PRESENT" if "index=0x86" in t else "no 0x86"))

    print("\n=== drive state WHILE ENABLED ===")
    show(read_axis_state())

    print("\n=== cali home ===")
    m = marker()
    print("   POST /calibrate/home -> %s" % (post("/calibrate/home"),))
    done = False
    counts = []
    for _ in range(20):
        time.sleep(1.5)
        t = fresh(m)
        c = re.findall(r"HomeNumdone : (\d+)", t)
        if c:
            counts.append(c[-1])
        if "servo calihome done" in t:
            done = True
            break
    print("   HomeNumdone sequence: %s" % (" -> ".join(counts) or "none"))
    for line in t.strip().splitlines()[-6:]:
        print("   " + line.strip())

    q = szf.joint_values()
    print("\npose after  : %s" % ", ".join("%+.4f" % v for v in q))
    print("calihome    : %s   max|q| = %.4f" % ("DONE" if done else "FAILED",
                                               max(abs(v) for v in q)))
    print("disable     -> %s" % (post("/settings/controlMode", '{"controlMode":"disable"}'),))
    time.sleep(2)
    print("final pose  : %s" % ", ".join("%+.4f" % v for v in szf.joint_values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
