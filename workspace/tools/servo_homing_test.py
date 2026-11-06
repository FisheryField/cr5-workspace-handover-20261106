#!/usr/bin/env python3
"""Decisive test: does this firmware implement CiA402 PROFILE HOMING at all?

CiA402 homing (mode 6) requires, minimally:
  * the controlword's bit4 (Homing operation start = 0x10) to be tested
  * 0x6098 Homing method to be read and compared (value 35 = current position)
  * 0x6060 Modes of operation to be set to 6 by the master

Established in this session:
  * descriptor field +0x1AE is the Controlword.  It is read at only TWO sites,
    and they test bit7 (0x80) and bit6 (0x40) - direction/reverse handling in the
    periodic position loop, not homing.
  * +0x2A4 (Homing method 0x6098) address is computed at exactly ONE site: the OD
    dispatcher handler.  No consumer computes that field address directly.

So test:
  (a) are there any other reads of field +0x1AE (any register, any width)?
  (b) is field +0x2A4 ever WRITTEN (i.e. does the master's SDO/PDO write land)?
  (c) is the constant 6 stored anywhere that could be "modes of operation"?
  (d) does anything write the Mode-of-Operation field +0x22C?
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x1AE, 0x2A4, 0x22C),
         ("3150", "data/servo_fw_samples/elf/v3150.bin", 0x1AE, 0x2A4, 0x22C)]


def addr_computers(insns, off):
    return [(i.address, i.mnemonic, i.op_str) for i in insns
            if i.mnemonic in ("addw", "add", "adds", "add.w")
            and re.search(r"#(0x%x|%d)\b" % (off, off), i.op_str)
            and "sp" not in i.op_str]


for label, path, cw, hm, moo in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    print("=" * 78)
    print("BUILD %s" % label)
    print("=" * 78)

    # (a) every access that uses a descriptor base with offset 0x1AE
    print("  (a) all accesses at [rX, #0x1ae] (Controlword):")
    for i in insns:
        if re.search(r"#0x1ae\]", i.op_str):
            print("       %08x %-9s %s" % (i.address, i.mnemonic, i.op_str))

    # (b) any store through an address computed with +0x2A4
    print()
    print("  (b) address computations with +0x%x (Homing method):" % hm)
    for a, m, o in addr_computers(insns, hm):
        print("       %08x %-9s %s" % (a, m, o))

    # (c) mode-of-operation field +0x22C
    print()
    print("  (c) address computations with +0x%x (Modes of operation):" % moo)
    for a, m, o in addr_computers(insns, moo):
        print("       %08x %-9s %s" % (a, m, o))

    # (d) is the value 6 stored right before something that looks like a mode field?
    print()
    print("  (d) `movs rX,#6` (candidate: enter mode 6 = homing):")
    n = 0
    for i in insns:
        if i.mnemonic == "movs" and re.search(r", #6$", i.op_str):
            n += 1
    print("       %d site(s) - too many to be conclusive" % n)
    print()
