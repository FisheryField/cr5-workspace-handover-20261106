#!/usr/bin/env python3
"""Find every write to the per-axis BASELINE field +0xA8 (and neighbours +0xAC).

Rationale: the closed 0x6064 chain is
    +0x238 (position actual)  <-  f( +0xA8 (baseline) + sl + 0x20000*fp, ... )
so the ONLY way 0x6064 can re-base to 0 is for +0xA8 to be re-anchored to the
current encoder reading.  Whoever writes +0xA8 is therefore the re-basing site -
the thing that differs between 3.2.D.8 and 3.1.5.0.

The descriptor array base is 0x2000138C (D8) / 0x2000129C (3150) with stride
0x329, so +0xA8 is reached either as `[rX,#0xa8]` (rX = descriptor pointer) or
via a literal base + offset.  Search both, and report read/write split.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x2000138C),
         ("3150", "data/servo_fw_samples/elf/v3150.bin", 0x2000129C)]

FIELDS = [0xA8, 0xAC, 0xB0, 0xB4, 0xA4, 0x9C]

WRITE_MN = ("str", "strb", "strh", "vstr", "strd")
READ_MN = ("ldr", "ldrb", "ldrh", "ldrsh", "ldrsb", "vldr")

for label, path, base in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}
    lit = resolve_literals(path)
    base_sites = sorted(a for a, (m, o, p, v) in lit.items() if v == base)

    print("=" * 78)
    print("BUILD %s : descriptor base 0x%08x loaded at %d site(s)" % (label, base, len(base_sites)))
    print("=" * 78)

    for f in FIELDS:
        writes, reads = [], []
        # (a) direct [rX, #f] on any register (excluding sp / pc)
        for i in insns:
            if "pc" in i.op_str:
                continue
            if not re.search(r"#0x%x\]" % f, i.op_str):
                continue
            if "sp" in i.op_str:
                continue
            (writes if i.mnemonic in WRITE_MN else reads).append(
                (i.address, i.mnemonic, i.op_str))
        # (b) through the descriptor base literal + offset
        for a in base_sites:
            reg = lit[a][1].split(",")[0].strip()
            cur = {reg}
            for j in range(idx[a], min(len(insns), idx[a] + 6)):
                i = insns[j]
                if i.address <= a:
                    continue
                if i.mnemonic in ("mov", "mov.w") and "," in i.op_str:
                    d, sm = [x.strip() for x in i.op_str.split(",")[:2]]
                    if sm in cur:
                        cur.add(d)
                if "[" in i.op_str and "pc" not in i.op_str and "sp" not in i.op_str:
                    ins = i.op_str.split("[", 1)[1]
                    for c in cur:
                        if re.match(r"\s*%s\b" % re.escape(c), ins) and \
                           re.search(r"#0x%x\]" % f, i.op_str):
                            (writes if i.mnemonic in WRITE_MN else reads).append(
                                (i.address, i.mnemonic, i.op_str))
        print("  +0x%03x : %2d write(s), %2d read(s)" % (f, len(writes), len(reads)))
        for a, m, o in writes[:10]:
            print("        WRITE %08x %-9s %s" % (a, m, o))
    print()
