#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Watch the controller while the robot is enabled, and give a verdict on
alarm 0x86 ("上使能关节位置偏差过大").

    python tools/watch_enable.py 90        # watch for 90 s

Start it, then enable the robot (DobotStudio or tools/enable_test.py).  It
polls the controller log and reports:
  * whether a fresh "settControlMode : enable" / "robot enabled" appeared
  * whether any NEW "AlarmSysSetBit index=0x86" line appeared in the window
  * the joint values before and after
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

GREP = ("L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -an 'settControlMode : \\|robot enabled\\|robot disabled\\|"
        "AlarmSysSetBit\\|not collision\\|enableRobot#40' $L | tail -25\n")


def snapshot():
    rc, out = szf.ssh_script(GREP, "watch")
    return out


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print("joint values before : %s"
          % ", ".join("%+.4f" % v for v in szf.joint_values()))
    before = snapshot()

    print("\n>>> now ENABLE the robot (you have %d s) <<<\n" % seconds)
    t0 = time.time()
    seen = before
    while time.time() - t0 < seconds:
        time.sleep(5)
        seen = snapshot()
        if "robot enabled" in seen and "robot enabled" not in before:
            break
        print("   ... %d s" % int(time.time() - t0))

    time.sleep(4)
    seen = snapshot()
    after_only = []
    nb = set(before.splitlines())
    for line in seen.splitlines():
        if line not in nb:
            after_only.append(line)

    print("\n--- new log lines ---")
    for line in after_only:
        print("   " + line.strip())

    enabled = any("robot enabled" in l for l in after_only)
    disabled = any("robot disabled" in l for l in after_only)
    alarm = any(re.search(r"index=0x86", l) for l in after_only)

    print("\njoint values after  : %s"
          % ", ".join("%+.4f" % v for v in szf.joint_values()))
    print()
    if alarm:
        print("VERDICT: alarm 0x86 DID fire -> the zero base of some axis still "
              "differs from the reported pose by >5 deg.")
        print("         roll back with: python tools\\rollback_to_stock.py")
    elif enabled and not disabled:
        print("VERDICT: OK - enable held and no 0x86 appeared.")
    elif enabled and disabled:
        print("VERDICT: the robot enabled and was then disabled, but NOT by "
              "0x86 - see the log above.")
    else:
        print("VERDICT: no enable was seen in the window.")
    return 1 if alarm else 0


if __name__ == "__main__":
    sys.exit(main())
