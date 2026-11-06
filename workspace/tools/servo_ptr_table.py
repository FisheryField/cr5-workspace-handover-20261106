#!/usr/bin/env python3
"""Locate the initialiser of the RAM function-pointer table 0x20000078 (D8) /
0x20000074 (3150), and dump the flash-resident table it is copied from.

Rationale: the last unresolved link in the 0x6064 position chain is
   +0x234 -> call table[+8] -> +0x238
where table = 0x20000078 (D8) / 0x20000074 (3150).  The table lives in RAM, so
a static image cannot show its contents - but its *initialiser* must exist, and
the source it copies from is a flash array whose contents we CAN read.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("data/servo_fw_samples/elf/v328d8.bin", "D8", 0x20000078),
         ("data/servo_fw_samples/elf/v3150.bin", "3150", 0x20000074)]


def flash_dword(code, addr):
    o = addr - FLASH_BASE
    if o < 0 or o + 4 > len(code):
        return None
    return int.from_bytes(code[o:o + 4], "little")


for path, label, tab in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = [i for i in md.disasm(code, FLASH_BASE)]
    idx = {i.address: k for k, i in enumerate(insns)}
    lit = resolve_literals(path)

    print("=" * 74)
    print("BUILD %s   function-pointer table base = 0x%08x" % (label, tab))
    print("=" * 74)

    # 1) any literal that points INTO flash (0x08000000..) and lands in a region
    #    whose first dwords look like code pointers -> candidate table source
    print("--- literals pointing into flash whose target looks like a pointer array ---")
    seen = set()
    for a, (m, o, p, v) in sorted(lit.items()):
        if not (0x08000000 <= v < 0x08100000):
            continue
        # sample 8 dwords
        ptrs = []
        for k in range(8):
            d = flash_dword(code, v + 4 * k)
            ptrs.append(d)
        # count how many look like Thumb code pointers
        good = sum(1 for d in ptrs if d and 0x08000000 <= (d & ~1) < 0x08100000)
        if good >= 6 and v not in seen:
            seen.add(v)
            print("  lit@%08x -> 0x%08x  (%d/8 look like code ptrs)" % (a, v, good))
            print("      " + " ".join("%08x" % d if d else "--------" for d in ptrs))

    # 2) direct stores into the table (str rX,[rY,#imm] with small imm) after
    #    loading the base literal nearby
    print()
    print("--- stores made through the table base (candidate table writes) ---")
    for a, (m, o, p, v) in sorted(lit.items()):
        if v != tab or m != "ldr":
            continue
        reg = o.split(",")[0].strip()
        for j in range(idx[a], min(len(insns), idx[a] + 8)):
            i = insns[j]
            if i.address <= a:
                continue
            if "[" in i.op_str and i.op_str.split("[", 1)[1].startswith(reg):
                kind = "WRITE" if i.mnemonic.startswith(("str", "vstr")) else "read "
                print("   %08x %-5s %-8s %s   (base lit @%08x)"
                      % (i.address, kind, i.mnemonic, i.op_str, a))
    print()
