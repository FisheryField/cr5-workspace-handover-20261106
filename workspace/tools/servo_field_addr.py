#!/usr/bin/env python3
"""Find every instruction that computes an address with a specific immediate
descriptor offset - i.e. the `addw rX, rY, #off` / `add.w` forms.

Why: the OD dispatcher handlers compute `&descriptor[axis] + off` with that exact
immediate, and any OTHER code reading the same descriptor field must compute the
same address the same way.  So searching for the immediate is the most reliable
way to find the true consumers of a field such as +0x2A4 (Homing method) or
+0x1AE (Controlword), independent of which register holds the base.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

# offsets of interest
FIELDS = {
    0x1AE: "Controlword 0x6040",
    0x1AF: "Statusword 0x6041",
    0x2A4: "Homing method 0x6098",
    0x2A0: "0x6098-adjacent",
    0x20C: "Home offset 0x607C",
    0x238: "Position actual value 0x6064",
    0x24C: "Target position 0x607A",
}

for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    print("=" * 78)
    print("BUILD %s : address computations with a given descriptor offset" % label)
    print("=" * 78)
    for off, name in FIELDS.items():
        hits = []
        for i in insns:
            o = i.op_str
            if i.mnemonic not in ("addw", "add", "adds", "add.w"):
                continue
            if not re.search(r"#(0x%x|%d)\b" % (off, off), o):
                continue
            hits.append((i.address, i.mnemonic, o))
        print("  +0x%03x (%-26s) : %2d site(s)" % (off, name, len(hits)))
        for a, m, o in hits[:10]:
            print("        %08x %-8s %s" % (a, m, o))
    print()
