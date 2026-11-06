#!/usr/bin/env python3
"""Audit descriptor field +0x36 and the +0xB8/+0xBA globals in both builds.

Hypothesis from reading D8 function 0x08010E60 line by line:

    r5 = &descriptor[axis]                     (0x2000138C + axis*0x329)
    g  = *(u16*)(0x200016B5 + 0xB8)             ; one-shot latch
    if (g == 0 && r4[+0x36] == 1) {             ; <- reinit condition
        r4[+0x30] = r5[+0x230]                  ; target position := reference
        r4[+0x20] = 0                           ; step = 0
        ...republish reference...
    }
    r4[+0x36] = g                               ; <<< descriptor latch update

So +0x36 is written from the global, and the global is what makes the reinit
one-shot.  This script verifies:
  (1) all sites computing/accessing +0x36
  (2) all accesses to the global 0x200016B5 at +0xB8 / +0xBA
  (3) whether the 3150 build has the same shape
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x200016B5),
         ("3150", "data/servo_fw_samples/elf/v3150.bin", 0x200016B5)]

for label, path, gbase in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}
    lit = resolve_literals(path)

    print("=" * 78)
    print("BUILD %s" % label)
    print("=" * 78)

    print("  (1) accesses at [rX, #0x36] (descriptor latch):")
    for i in insns:
        if re.search(r"#0x36\]", i.op_str) and "sp" not in i.op_str:
            print("       %08x %-9s %s" % (i.address, i.mnemonic, i.op_str))

    print()
    print("  (2) accesses through the global pointer 0x%08x:" % gbase)
    sites = sorted(a for a, (m, o, p, v) in lit.items() if v == gbase)
    print("      %d literal load site(s): %s" % (len(sites), [hex(s) for s in sites[:12]]))
    for a in sites:
        reg = lit[a][1].split(",")[0].strip()
        for j in range(idx[a], min(len(insns), idx[a] + 4)):
            i = insns[j]
            if i.address <= a:
                continue
            if re.search(r"\[%s, #0x(b8|ba)\]" % re.escape(reg), i.op_str):
                print("       %08x  %-9s %s   (lit @%08x)"
                      % (i.address, i.mnemonic, i.op_str, a))
    print()
