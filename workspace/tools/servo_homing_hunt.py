#!/usr/bin/env python3
"""Locate the CiA402 homing consumers in the servo firmware.

Facts established earlier:
  * object 0x6098 (Homing method) is served by a handler whose ONLY job is
    `str r3,[r0,#0x18]` where r3 = &descriptor[axis] + 0x2A4  - i.e. it merely
    publishes the field ADDRESS.  The logic is elsewhere.
  * the known Homing method in use is 35 (0x23), and CiA402 homing is triggered
    from the controlword, whose descriptor offset is 0x1AE.

So search for:
  (1) direct reads of descriptor field +0x2A4
  (2) the constant 35 as an immediate (movs/movw #0x23) - the homing method value
  (3) consumers of the controlword field +0x1AE, especially bit tests
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

FIELDS = [0x2A4, 0x2A0, 0x1AE, 0x1AF]      # homing method, target velocity?, cw, sw

for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    print("=" * 78)
    print("BUILD %s" % label)
    print("=" * 78)

    print("--- (1) direct accesses to descriptor fields ---")
    for f in FIELDS:
        hits = []
        for i in insns:
            if "[" not in i.op_str or "pc" in i.op_str:
                continue
            if re.search(r"#0x%x\]" % f, i.op_str):
                hits.append((i.address, i.mnemonic, i.op_str))
        kind = "r/w"
        print("   +0x%03x : %2d site(s)" % (f, len(hits)))
        for a, m, o in hits[:8]:
            print("        %08x %-8s %s" % (a, m, o))

    print()
    print("--- (2) constant 35 (0x23 = Homing method) as an immediate ---")
    hits = []
    for i in insns:
        if i.mnemonic in ("movs", "mov", "mov.w", "cmp") and \
           re.search(r", #0x23\b", i.op_str):
            hits.append((i.address, i.mnemonic, i.op_str))
    print("   %d site(s)" % len(hits))
    for a, m, o in hits[:24]:
        print("        %08x %-8s %s" % (a, m, o))
    print()
