#!/usr/bin/env python3
"""Decode the servo CiA402 OD dispatcher into a complete
        object index  ->  per-axis descriptor field offset
table, for both builds.

HANDLER SHAPE (uniform across the whole table; this is the key discovery):
    movw r3,#0x329 ; muls r3,r2,r3        ; r2 = axis
    ldr  r4,=<base>                        ; per-axis descriptor array base
    add  r3,r4 / addw r3,r3,#<off>         ; r3 = &descriptor[axis].field
    str  r3,[r0,#0x18]                     ; hand the field address to the core
    b    <common tail>
So every OD entry is just "expose descriptor byte <off> as this object", and the
dispatcher therefore yields an authoritative index -> struct-offset map.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

STRIDE = 0x329


for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    lit = resolve_literals(path)

    print("=" * 76)
    print("BUILD %s  : descriptor field-offset table" % label)
    print("=" * 76)

    entries = []
    for k, ins in enumerate(insns):
        if ins.mnemonic != "movw" or not re.search(r"#0x%x\b" % STRIDE, ins.op_str):
            continue
        off = base = None
        for j in range(k, min(len(insns), k + 8)):
            a, m, o = insns[j].address, insns[j].mnemonic, insns[j].op_str
            if a in lit:
                base = lit[a][3]
            mm = re.search(r"#(0x[0-9a-f]+)\b", o)
            if m in ("addw", "add.w", "add") and "r3" in o and mm:
                off = int(mm.group(1), 16)
        if off is not None:
            entries.append((ins.address, base, off))

    print("  handler stubs found: %d" % len(entries))
    seen = {}
    for a, base, off in entries:
        seen.setdefault((base, off), []).append(a)
    print("  distinct (base, offset) pairs: %d" % len(seen))

    bases = {}
    for (b, _o) in seen:
        bases[b] = bases.get(b, 0) + 1
    print("  bases seen: %s"
          % ", ".join("0x%08x(x%d)" % (b, n) for b, n in sorted(bases.items(), key=lambda kv: -kv[1])))
    print()
    print("  offset    base        first handler")
    for (base, off) in sorted(seen, key=lambda t: (t[1] if t[1] is not None else -1)):
        hs = sorted(seen[(base, off)])
        print("  0x%03x     0x%08x  %s" % (off, base or 0, " ".join("%08x" % h for h in hs[:3])))
    print()
