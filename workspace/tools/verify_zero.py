#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only zero / patch verifier (run at step 3 and step 5 of the runbook).

    python tools/verify_zero.py

Prints
  1. the six reported joint angles (TCP 30005)
  2. whether the robot is currently enabled or disabled (from the log)
  3. what the PLC mapped into each slave's 0x1A00 -> stock or patched
  4. a verdict, interpreted per state:

  * DISABLED: the reported value is the drive's re-based position 0x6064,
    i.e. the true joint value.  After a successful calibration all six must be
    ~0; 110..144 deg means the zero bases are still the damaged ones.
  * ENABLED + stock app: the reported value is 0x6062, which on 3.1.5.0 is the
    raw absolute encoder angle (8..35 deg here) - NOT an error, and NOT a
    usable check of the zero.
  * ENABLED + patched app: the reported value is 0x6064 again (the true joint
    value) and must be ~0 with no alarm 0x86.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402


def main():
    q = szf.joint_values()
    rc, out = szf.ssh_script(
        "L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -a 'settControlMode : \\|robot enabled\\|robot disabled' $L | tail -3\n",
        "mode")
    enabled = False
    for line in out.splitlines():
        if "settControlMode : enable" in line or "robot enabled" in line:
            enabled = True
        if "settControlMode : disable" in line or "robot disabled" in line:
            enabled = False

    per, order = szf.mapping_state()
    patched = None
    print("=" * 72)
    print("1) reported joint angles (TCP 30005)")
    print("=" * 72)
    for i, v in enumerate(q):
        print("   J%d = %+12.6f deg" % (i + 1, v))
    print()
    print("=" * 72)
    print("2) control mode now : %s" % ("ENABLED" if enabled else "DISABLED"))
    print("=" * 72)
    for line in out.strip().splitlines():
        print("   " + line.strip())
    print()
    print("=" * 72)
    print("3) per-slave TxPDO mapping (0x1A00) - stock or patched")
    print("=" * 72)
    for addr in sorted(per):
        subs = per[addr]
        n = subs.get(0)
        last = subs.get(int(n, 16)) if n else None
        name = "?"
        for k, s in enumerate(szf.SLAVE_OF_TABLE):
            if addr in (1000 + s, s):
                name = szf.AXIS_OF_SLAVE[s]
        if last == "60640020" and subs.get(3) == "60620020":
            state = "PATCHED (reports 0x6064)"
        elif last == "60620020" and subs.get(3) == "60640020":
            state = "stock   (reports 0x6062)"
        else:
            state = "UNKNOWN"
        patched = (state.startswith("PATCHED")) if patched is None else patched
        print("   %-5d %-3s entries=%-4s record2=%-10s last=%-10s %s"
              % (addr, name, n, subs.get(3), last, state))
    print()
    print("=" * 72)
    mx = max(abs(v) for v in q)
    if not enabled:
        if mx < 0.5:
            verdict = "zero is VALID - all six joints read ~0 while disabled"
        else:
            verdict = ("zero bases are still NOT valid (max |q| = %.3f deg; "
                       "expect ~0 after a successful calibration)" % mx)
    elif patched:
        verdict = ("patched app while enabled: reported = 0x6064; must be ~0 "
                   "and stay enabled (max |q| = %.3f deg)" % mx)
    else:
        verdict = ("stock app while enabled: reported = 0x6062 = raw absolute "
                   "angle (%.1f..%.1f deg) - normal on 3.1.5.0, use the "
                   "DISABLED reading to judge the zero"
                   % (min(q), max(q)))
    print("VERDICT: %s" % verdict)
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
