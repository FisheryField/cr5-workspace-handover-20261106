#!/usr/bin/env python3
"""Enumerate every flash literal that points into the low RAM block
0x20000000..0x20000200 - the region holding the function-pointer table at
0x20000078 (D8) / 0x20000074 (3150).

Purpose: the table is read via `ldr rX,=<base>; ldr rY,[rX,#n]; blx rY` in 30+
sites but is never written by any instruction.  Enumerating every distinct
target in the block, and how many sites reference it, shows which addresses are
"live" and which sub-block might be bulk-initialised.
"""
import sys
from collections import defaultdict

sys.path.insert(0, "tools")

from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

for label, path in CASES:
    lit = resolve_literals(path)
    block = defaultdict(list)
    for a, (m, o, p, v) in sorted(lit.items()):
        if 0x20000000 <= v < 0x20000200:
            block[v].append(a)

    print("=" * 74)
    print("BUILD %s : flash literals into 0x20000000..0x20000200" % label)
    print("=" * 74)
    print("  %d distinct targets" % len(block))
    print()
    print("  target      sites  example site(s)")
    for v in sorted(block):
        s = sorted(block[v])
        print("  0x%08x  %4d   %s" % (v, len(s),
                                      " ".join("%08x" % x for x in s[:4])))

    # which targets are used as a base with an immediate offset (table-like)?
    print()
    print("  --- targets that are dereferenced with an offset (candidate tables) ---")
    from servo_img import FLASH_BASE, load_image, make_md
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}
    for v in sorted(block):
        offs = set()
        for a in block[v]:
            reg = lit[a][1].split(",")[0].strip()
            for j in range(idx[a], min(len(insns), idx[a] + 4)):
                i = insns[j]
                if i.address <= a:
                    continue
                if i.op_str.startswith(reg + ",") or \
                   ("[" + reg) in i.op_str or ("[" + reg + ",") in i.op_str:
                    import re
                    mm = re.search(r"#(0x[0-9a-f]+)\b", i.op_str)
                    if mm and "[" in i.op_str:
                        offs.add(int(mm.group(1), 16))
        if offs:
            print("   0x%08x : offsets %s" % (v, sorted(hex(x) for x in offs)[:14]))
    print()
