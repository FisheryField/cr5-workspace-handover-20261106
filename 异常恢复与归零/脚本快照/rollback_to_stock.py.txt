#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roll the PLC application back to the PRISTINE vendor build.

Reason (field evidence, 2026-09-24):
  * The patched build makes the master read 0x6064 (re-based) as the joint
    value.  With the servo zero bases damaged by the re-flash those values are
    110..144 deg, and the controller latches alarm 0x86 ("上使能关节位置偏差
    过大") 0.14 s after every enable and drops back to disabled.
  * The stock build reads 0x6062, which on 3.1.5.0 carries the raw absolute
    angle while enabled: measured -8.13 / +10.25 / +8.81 / +1.95 / +7.39 /
    +20.5 deg.  Those are small enough to pass (J6 lived with 20.5 deg), so the
    enable should hold - which is what is needed to be able to move the arm and
    run the zero calibration.

Touches: <variant>/Application.app + .crc  (from BACKUP_ORIGINAL),
         Recipe/Update.txt back to the vendor value 777, then reboot.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

ORIG = "/dobot/userdata/codesys/BACKUP_ORIGINAL"
UPDATE = "/home/ftp/PlcLogic/Recipe/Update.txt"


def main():
    v = szf.variant_dir()
    print("variant dir : %s" % v)
    script = """#!/bin/sh
set -e
echo "--- before ---"
md5sum %s/Application.app %s/Application.app
echo "--- pristine source ---"
md5sum %s/Application.app
cp -a %s/Application.app %s/Application.app
cp -a %s/Application.crc %s/Application.crc
echo 777 > %s
echo "--- after ---"
md5sum %s/Application.app
od -An -tx1 %s/Application.crc
echo -n "Update.txt = "; cat %s
""" % (v, szf.LIVE_DIR, ORIG, ORIG, v, ORIG, v, UPDATE, v, v, UPDATE)
    rc, out = szf.ssh_script(script, "rollback_orig")
    print(out.strip())
    if rc != 0:
        raise SystemExit("!! rollback FAILED - nothing rebooted")
    print("\nrebooting ...")
    szf.ssh_script("sync\nreboot\n", "reboot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
