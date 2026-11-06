#!/usr/bin/env python3
"""Find flash-resident arrays of Thumb code pointers (candidate .init_array /
dispatch tables) whose contents could be what fills the RAM table at
0x20000078 (D8) / 0x20000074 (3150).

A code-pointer array in flash looks like a run of dwords, each of which is
0x08000000..0x08100000 with bit0 = 1 (Thumb).  Any such run is a candidate
source for a startup copy into the RAM function-pointer table.
"""
import struct
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

MIN_RUN = 4


def is_code_ptr(v, lo, hi):
    return lo <= (v & ~1) < hi and (v & 1) == 1


for label, path in CASES:
    _r, _h, code = load_image(path)
    print("=" * 76)
    print("BUILD %s : runs of Thumb code pointers in flash" % label)
    print("=" * 76)

    runs = []
    i = 0
    n = len(code)
    while i + 4 <= n:
        v = struct.unpack_from("<I", code, i)[0]
        if is_code_ptr(v, 0x08000000, 0x08100000):
            j = i
            run = []
            while j + 4 <= n:
                w = struct.unpack_from("<I", code, j)[0]
                if is_code_ptr(w, 0x08000000, 0x08100000):
                    run.append(w)
                    j += 4
                else:
                    break
            if len(run) >= MIN_RUN:
                runs.append((i + FLASH_BASE, run))
            i = j
        else:
            i += 4

    # filter out literal pools: a literal pool is PRECEDED by code that loads
    # from it, and its entries are usually a mix; keep runs of >=6 for reporting
    runs.sort(key=lambda t: -len(t[1]))
    print("  runs of >=%d code pointers: %d" % (MIN_RUN, len(runs)))
    for addr, run in runs[:14]:
        print("   @0x%08x  len=%d" % (addr, len(run)))
        print("       " + " ".join("%08x" % w for w in run[:10])
              + (" ..." if len(run) > 10 else ""))
    print()
