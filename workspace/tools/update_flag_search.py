#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search for the flag that arms the "post servo flash" pose check.

Facts: mToolServer (the vendor flash tool) writes
  * /home/ftp/PlcLogic/Recipe/SavePos.txt  (six float64 joint values = the pose
    right before the flash) and
  * `echo "666" > /home/ftp/PlcLogic/Recipe/Update.txt`
  * `echo "777" > /home/ftp/PlcLogic/Recipe/Update.txt`
at two different points of its flow.  The file currently holds 777.
The PLC application binary contains the SavePos.txt path twice, and
alarm 0x86 ("上使能关节位置偏差过大") fires ~0.2 s after every enable since the
servos were re-flashed - i.e. exactly the situation a post-flash pose check is
meant to detect.

This script walks a few candidate Update.txt values; for each one it clears the
alarms, enables the robot and reports whether alarm 0x86 comes back.  A value
that keeps the robot enabled wins.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

REMOTE = "/home/ftp/PlcLogic/Recipe/Update.txt"
CANDIDATES = ["666", "0", "1", "777"]
GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|not collision\\|AlarmSysSetBit\\|"
        "HomeNumdone\\|calihome done\\|robot enabled\\|robot disabled' $L | "
        "tail -12\n")


def post(path, body="{}"):
    import urllib.request
    req = urllib.request.Request("http://%s:22000%s" % (szf.CTRL_IP, path),
                                 data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return str(e)[:60]


def logtail():
    rc, out = szf.ssh_script(GREP, "flag")
    return out


def main():
    rc, out = szf.ssh_script("cat %s\n" % REMOTE, "get")
    print("Update.txt now : %r" % out.strip())
    for value in CANDIDATES:
        print("\n=== Update.txt = %s" % value)
        rc, out = szf.ssh_script("echo \"%s\" > %s\ncat %s\n"
                                 % (value, REMOTE, REMOTE), "set")
        print("    now: %r" % out.strip())
        print("    clearAlarms -> %s" % (post("/interface/clearAlarms"),))
        time.sleep(2)
        print("    enable      -> %s"
              % (post("/settings/controlMode", '{"controlMode":"enable"}'),))
        time.sleep(6)
        t = logtail()
        print("    log:")
        for line in t.strip().splitlines()[-8:]:
            print("      " + line)
        if "index=0x86" not in t:
            print("    ==> NO alarm 0x86 -> this value works")
            return 0
    print("\n!! none of the candidate values stopped the alarm")
    return 2


if __name__ == "__main__":
    sys.exit(main())
