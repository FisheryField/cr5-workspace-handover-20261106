#!/usr/bin/env python3
"""Discriminant test: does build B contain the D8 "one-shot position-command
reinitialisation" data flow?

D8 0x08010E60 contains this exact data flow (read line by line):

    <gate on *(0x200016B5+0xB8)>  and  <?+0x36 == 1>
        <?+0x230>  ->  <?+0x30>      ; target position := reference
        <?+0x20> = 0                 ; step := 0
        ...
    <?+0x36> := <gate>               ; latch updated unconditionally

The COMPILED SIGNATURE that is independent of address, register and field-offset
relocation is this local adjacency within a single basic block:

    ldr.w  rX, [rA, #imm]        ; read reference
    str    rX, [rB, #imm2]       ; write target position
    movs   rZ, #0
    str    rZ, [rB, #imm3]       ; clear step

i.e. load, store, `movs #0`, store - four consecutive instructions.

This script looks for that exact four-instruction shape and reports each hit with
its address, so the D8 and 3150 populations can be compared.  It prints D8 first
as the positive control (the pattern MUST be found there).
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]


def find_shape(insns):
    """ldr.w rX,[..] ; str rX,[..] ; movs rZ,#0 ; str rZ,[..]"""
    hits = []
    for k in range(len(insns) - 3):
        a, b, c, d = insns[k], insns[k + 1], insns[k + 2], insns[k + 3]
        if not a.mnemonic.startswith("ldr") or "[" not in a.op_str:
            continue
        ra = a.op_str.split(",")[0].strip()
        if not re.match(r"^r(?!0\b)\d+$", ra):      # must be a real load into rN
            continue
        if not b.mnemonic.startswith("str") or "[" not in b.op_str:
            continue
        if b.op_str.split(",")[0].strip() != ra:
            continue
        if c.mnemonic != "movs" or not c.op_str.endswith(", #0"):
            continue
        rc = c.op_str.split(",")[0].strip()
        if not d.mnemonic.startswith("str") or "[" not in d.op_str:
            continue
        if d.op_str.split(",")[0].strip() != rc:
            continue
        hits.append((a.address, a.mnemonic, a.op_str, b.op_str, d.op_str))
    return hits


for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    hits = find_shape(insns)
    print("=" * 78)
    print("BUILD %s : 'ldr rX,[..] / str rX,[..] / movs rZ,#0 / str rZ,[..]' : %d hit(s)"
          % (label, len(hits)))
    print("=" * 78)
    for addr, m, o, b, d in hits[:30]:
        print("   %08x  %s %s | %s | %s" % (addr, m, o, b, d))
    print()
