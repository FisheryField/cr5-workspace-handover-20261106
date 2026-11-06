#!/usr/bin/env python3
"""Dump every distinct 16-bit immediate loaded by movw/movt in a servo build.

Purpose: the OD dispatcher uses SPARSE binary-search pivots (0x608e/0x6072/
0x6064/0x605c/0x6041) plus `tbb` jump tables inside each range, so absence of a
`movw #0x607c` does NOT prove the index is unimplemented.  Listing the actual
immediate population shows which indices are compared directly at all.
"""
import sys
from collections import defaultdict

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image


def all_imm16(code):
    """reg -> set of immediate values, plus a value -> sites map."""
    sites = defaultdict(list)
    for o in range(0, len(code) - 4, 2):
        w1 = int.from_bytes(code[o:o + 2], "little")
        if (w1 & 0xF800) != 0xF000:
            continue
        top = (w1 >> 4) & 0x1F
        if top not in (0x04, 0x0C):
            continue
        w2 = int.from_bytes(code[o + 2:o + 4], "little")
        imm16 = ((w1 & 0xF) << 12) | (((w1 >> 10) & 1) << 11) \
                | (((w2 >> 12) & 0x7) << 8) | (w2 & 0xFF)
        rd = (w2 >> 8) & 0xF
        kind = "movw" if top == 0x04 else "movt"
        sites[imm16].append((o + FLASH_BASE, kind, rd))
    return sites


for path, label in (("data/servo_fw_samples/elf/v328d8.bin", "D8"),
                    ("data/servo_fw_samples/elf/v3150.bin", "3150")):
    _r, _h, code = load_image(path)
    sites = all_imm16(code)
    print("=" * 72)
    print("BUILD %s : %d distinct imm16 values" % (label, len(sites)))
    print("=" * 72)
    odv = sorted(v for v in sites if 0x6000 <= v <= 0x60FF)
    print("--- immediates in the CiA402 index range 0x6000..0x60FF : %d ---" % len(odv))
    for v in odv:
        s = sorted(sites[v])
        print("   0x%04X  x%-2d  %s" % (v, len(s), " ".join("%08x/%s" % (a, k) for a, k, _ in s[:5])))
    print()
