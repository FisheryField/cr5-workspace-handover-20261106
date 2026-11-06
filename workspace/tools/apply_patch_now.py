#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the six-axis TxPDO patch (step 4 of ZERO_RECOVERY_RUNBOOK.md).

    python tools/apply_patch_now.py            install + reboot + verify
    python tools/apply_patch_now.py --verify   read-only status, no changes

Run this ONLY after the zero calibration has been done and verified
(tools/servo_zero_fix.py check -> 0x6064 == 0 on all six axes).  Installing it
while the servo zero bases are still damaged reproduces alarm 0x86
(|controller pose - reported pose| > 5.0 deg).
"""
import argparse
import hashlib
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

APP = os.path.join(szf.ROOT, "data", "cabinet", "Application_fixed_all6.app")
CRC = os.path.join(szf.ROOT, "data", "cabinet", "Application_fixed_all6.crc")
WANT_MD5 = "9a808cd9dd8f3aa6adaa4de1a34eb9b3"

STATUS = ("md5sum %s/Application.app %s/Application.app\n"
          "od -An -tx1 %s/Application.crc\n")


def status():
    v = szf.variant_dir()
    rc, out = szf.ssh_script(STATUS % (v, szf.LIVE_DIR, v), "status")
    print(out.strip())
    live = [l.split()[0] for l in out.splitlines() if l.strip().endswith("Application.app")]
    which = "PATCHED" if WANT_MD5 in live else "stock/other"
    print("=> live application is: %s" % which)
    return v, live


def verify():
    print("=" * 70)
    print("1) reported joint angles (TCP 30005)")
    print("=" * 70)
    a = szf.joint_values()
    for i, v in enumerate(a):
        print("   J%d = %+12.6f deg   = %+10.1f counts"
              % (i + 1, v, v / szf.SCALE))
    print()
    print("=" * 70)
    print("2) what the master mapped into 0x1A00 this boot")
    print("=" * 70)
    per, order = szf.mapping_state()
    for addr in sorted(per):
        subs = per[addr]
        n = subs.get(0)
        last = subs.get(int(n, 16)) if n else None
        name = "?"
        for k, s in enumerate(szf.SLAVE_OF_TABLE):
            if addr in (1000 + s, s):
                name = szf.AXIS_OF_SLAVE[s]
        print("   %-5d %-3s entries=%-4s record2=%-10s last=%-10s"
              % (addr, name, n, subs.get(3), last))
    print()
    print("=" * 70)
    print("3) alarm 0x86 activity in the log (should be 0 while nothing is enabled)")
    print("=" * 70)
    rc, out = szf.ssh_script(
        "L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "echo -n 'AlarmSysSetBit index=0x86 total lines: '\n"
        "grep -ac 'AlarmSysSetBit()#40[67]] index=0x86' $L\n"
        "echo -n 'last 0x86 line: '\n"
        "grep -a 'AlarmSysSetBit()#40[67]] index=0x86' $L | tail -1\n"
        "echo '--- last control-mode lines ---'\n"
        "grep -a 'settControlMode : \\|robot enabled\\|robot disabled' $L | tail -5\n",
        "alarm")
    print(out.strip())
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="only report the current state")
    args = ap.parse_args()

    print("--- pre-flight on the patch pair ---")
    rc = subprocess.call([sys.executable,
                          os.path.join(szf.ROOT, "tools", "patch_preflight.py")])
    if rc != 0:
        raise SystemExit("!! pre-flight FAILED - not installing")

    if args.verify:
        print()
        status()
        print()
        return verify()

    print("\n--- current application ---")
    status()
    print("\n--- installing (auto-backup) ---")
    rc = subprocess.call([sys.executable,
                          os.path.join(szf.ROOT, "tools", "servo_zero_fix.py"),
                          "install", APP, CRC])
    if rc != 0:
        raise SystemExit("!! install FAILED - nothing rebooted")

    print("\n--- rebooting the controller ---")
    szf.ssh_script("sync\nreboot\n", "reboot")
    print("waiting 115 s ...")
    time.sleep(115)

    print("\n--- after reboot ---")
    v, live = status()
    if WANT_MD5 not in live:
        print("!! the patched application is NOT live - check %s" % v)
        return 2
    print()
    verify()
    print()
    print("NEXT: enable the robot, then run")
    print("   python tools\\watch_enable.py 90")
    print("and confirm that no 'index=0x86' appears.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
