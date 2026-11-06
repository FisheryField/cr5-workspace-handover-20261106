#!/usr/bin/env python3
"""Examine every flash-resident dword equal to the function-pointer-table base
(0x20000078 in D8 / 0x20000074 in 3150) and ask: is any of them a SYMBOL
pointing at a flash array of code pointers (i.e. the table's initialiser data)?

Background: the table is read via `ldr rX,=<base>; ldr rY,[rX,#n]; blx rY`
in 30+ places, but NO instruction writes it.  Two remaining explanations:
  (a) it is bulk-copied from a flash initialiser image during startup
  (b) it is filled by code that addresses it through a computed/aliased pointer
If (a), some dword in flash must point at the initialiser array; this script
looks for candidates by checking whether the dword is followed by a run of
plausible Thumb code pointers (which is what a .init_array / dispatch table
looks like).
"""
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image


def dword(code, addr):
    o = addr - FLASH_BASE
    if o < 0 or o + 4 > len(code):
        return None
    return int.from_bytes(code[o:o + 4], "little")


def looks_like_code_ptr(v):
    return v is not None and 0x08000000 <= (v & ~1) < 0x08100000


for path, lab, tab in (("data/servo_fw_samples/elf/v328d8.bin", "D8", 0x20000078),
                       ("data/servo_fw_samples/elf/v3150.bin", "3150", 0x20000074)):
    _r, _h, code = load_image(path)
    needle = tab.to_bytes(4, "little")
    hits = []
    i = code.find(needle)
    while i >= 0:
        hits.append(i + FLASH_BASE)
        i = code.find(needle, i + 1)

    print("=" * 76)
    print("BUILD %s : %d dword occurrence(s) of 0x%08x" % (lab, len(hits), tab))
    print("=" * 76)

    for a in hits:
        # what surrounds it?
        before = [dword(code, a - 4 * k) for k in (2, 1)]
        after = [dword(code, a + 4 * k) for k in (1, 2, 3, 4)]
        n_after_code = sum(1 for v in after if looks_like_code_ptr(v))
        tag = "  <== CANDIDATE initialiser table" if n_after_code >= 3 else ""
        print(" @0x%08x" % a)
        print("     -8: %s   -4: %s" % (
            " ".join("%08x" % v if v is not None else "--------" for v in before[:1]),
            " ".join("%08x" % v if v is not None else "--------" for v in before[1:])))
        print("     +4..+20: %s   (code-ptr-like after: %d)"
              % (" ".join("%08x" % v if v is not None else "--------" for v in after),
                 n_after_code), )
        if tag:
            print(tag)
    print()

    # Also: does any flash dword point AT a region that contains the base dword,
    # i.e. an initialiser record {dst, src, len}?
    print("--- searching for {dst=0x%08x, src, len} style records ---" % tab)
    found = 0
    for o in range(0, len(code) - 12, 4):
        d = int.from_bytes(code[o:o + 4], "little")
        if d != tab:
            continue
        src = int.from_bytes(code[o + 4:o + 8], "little")
        ln = int.from_bytes(code[o + 8:o + 12], "little")
        if 0x08000000 <= src < 0x08100000 and 0 < ln <= 0x400:
            print("   @0x%08x  dst=0x%08x src=0x%08x len=0x%x"
                  % (o + FLASH_BASE, d, src, ln))
            found += 1
    if not found:
        print("   none")
    print()
