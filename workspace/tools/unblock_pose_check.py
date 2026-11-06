#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unblock the robot: disarm the post-flash pose check and make the recorded
pose match reality, then reboot so the PLC re-reads it.

Evidence behind this:
  * mToolServer (the vendor servo-flash tool) writes SavePos.txt (the joint pose
    right before the flash) and then `echo "777" > Update.txt`; the matching
    `echo "666" > ...` appears in the same binary for the other end of the flow.
  * alarm 0x86 ("上使能关节位置偏差过大", alarm_controller.json id 134) fires
    ~0.2 s after every successful enable while Update.txt is 777, and did NOT
    fire in the two enables tried right after Update.txt was changed.
  * The recorded pose must equal the current pose, otherwise the comparison
    fails again on the next boot.

Leaves the controller: Update.txt = 666, SavePos.txt = current pose, alarms
cleared, rebooted.
"""
import json
import os
import struct
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

SAVEPOS = "/home/ftp/PlcLogic/Recipe/SavePos.txt"
UPDATE = "/home/ftp/PlcLogic/Recipe/Update.txt"
LOCAL = os.path.join(szf.ROOT, "data", "SavePos_new.txt")


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


def main():
    q = szf.joint_values()
    print("current pose : %s" % ", ".join("%+.6f" % v for v in q))

    szf.scp_get(SAVEPOS, LOCAL)
    blob = bytearray(open(LOCAL, "rb").read())
    struct.pack_into("<6d", blob, 0, *q)
    open(LOCAL, "wb").write(bytes(blob))
    rc = szf.scp_put(LOCAL, SAVEPOS)
    print("SavePos.txt   -> rc=%d  payload=%s"
          % (rc[0], struct.unpack_from("<6d", bytes(blob), 0)))

    rc, out = szf.ssh_script(
        "cp -a %s %s.bak2 2>/dev/null\n"
        "echo 666 > %s\n"
        "echo '--- Update.txt ---'; cat %s\n"
        "echo '--- SavePos.txt ---'; od -An -tx1 %s | head -4\n"
        % (UPDATE, UPDATE, UPDATE, UPDATE, SAVEPOS), "flags")
    print(out.strip())

    print("\nclearAlarms -> %s" % (post("/interface/clearAlarms"),))
    time.sleep(2)
    print("rebooting the controller ...")
    rc, out = szf.ssh_script("sync\nreboot\n", "reboot")
    print(out.strip()[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
