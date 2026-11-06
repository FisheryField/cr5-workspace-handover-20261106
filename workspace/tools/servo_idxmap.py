#!/usr/bin/env python3
"""Resolve the FULL CiA402 index set served by the servo OD dispatcher.

The dispatcher (D8 0x0800289C / 3150 0x080027B8) tests 5 sparse pivots and then
resolves each gap with `cmp #imm` pairs and `tbb`/`tbh` jump tables.  Recovering
the *exact* index list matters because it tells us which OD objects the firmware
actually serves - in particular whether any of the manufacturer-specific /
vendor objects are readable (they would be the only in-band way to get data out
of a drive, since the firmware has no UART and FoE is write-only).

Method: walk the dispatch tree explicitly, tracking the index range that reaches
each tbb/tbh table, then map table slot k -> index = range_base + k.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]


def table_entries(code, insn_addr, count, halfword):
    """Resolve a tbb/tbh table placed immediately after the instruction."""
    base = insn_addr + 4
    out = []
    for k in range(count):
        if halfword:
            o = insn_addr + 4 - FLASH_BASE + 2 * k
            v = int.from_bytes(code[o:o + 2], "little")
            out.append(base + 2 * v)
        else:
            o = insn_addr + 4 - FLASH_BASE + k
            v = code[o]
            out.append(base + 2 * v)
    return out


for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    print("=" * 78)
    print("BUILD %s : complete served-index map" % label)
    print("=" * 78)

    # locate every tbb/tbh that resolves into the handler region
    tables = []
    for i in insns:
        if i.mnemonic == "tbh":
            cnt, hw = 0x38, True
        elif i.mnemonic == "tbb":
            cnt, hw = 0x40, False
        else:
            continue
        e = table_entries(code, i.address, 8, hw)
        if all(0x08002000 <= t <= 0x08032000 for t in e):
            tables.append((i.address, i.mnemonic, hw))
    print("  candidate jump tables (resolve into handler region):")
    for a, m, hw in tables:
        print("    %08x %s" % (a, m))
    print()

    # For each table, print the first N entries as resolved handler addresses,
    # which is what identifies "slot k is implemented".
    for a, m, hw in tables:
        n = 0x38 if hw else 0x40
        e = table_entries(code, a, n, hw)
        print("  --- %s @%08x : %d slots ---" % (m, a, n))
        prev = None
        for k, t in enumerate(e):
            if t != prev:
                print("      k=%-3d -> %08x" % (k, t))
            prev = t
        print()
