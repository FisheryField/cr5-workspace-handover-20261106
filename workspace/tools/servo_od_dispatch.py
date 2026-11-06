#!/usr/bin/env python3
"""# [DEFECTIVE for tbh] Resolve the servo OD dispatcher index map.

KNOWN DEFECT (found 2026-09-24, round 31): the `tbh` halfword table base
and/or entry scaling here is WRONG.  Two independent attempts to auto-resolve
the dispatcher tree produced *inconsistent* handler addresses, and neither
reproduced the one mapping that was established by hand.

DO NOT trust this script's index -> handler output.

What IS reliable (established by hand, cited in SERVO_SUMMARY.md 12.4):
    0x6064 -> handler 0x08002BBC -> descriptor offset +0x238
plus the (handler, descriptor-offset) pair list produced by
tools/servo_od_fieldextract.py.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]


def load(path):
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    return code, insns, {i.address: k for k, i in enumerate(insns)}


def resolve_tbb(code, insns, idx, count, halfword):
    """Resolve a tbb/tbh jump table following the instruction."""
    ins = insns[idx]
    base = ins.address + 4
    out = []
    for k in range(count):
        if halfword:
            o = ins.address + 4 - FLASH_BASE + 2 * k
            v = int.from_bytes(code[o:o + 2], "little")
            out.append(base + 2 * v)
        else:
            o = ins.address + 4 - FLASH_BASE + k
            v = code[o]
            out.append(base + 2 * v)
    return out


for label, path in CASES:
    code, insns, idx = load(path)
    print("=" * 74)
    print("BUILD %s : OD dispatcher index map" % label)
    print("=" * 74)

    # Each build has its own dispatcher base; locate the tbh by scanning the
    # whole image for a tbh whose offset table resolves into the handler region.
    big = None
    for i in insns:
        if i.mnemonic != "tbh" or "pc" not in i.op_str:
            continue
        base = i.address + 4
        good = 0
        for k in range(4):
            o = i.address + 4 - FLASH_BASE + 2 * k
            v = int.from_bytes(code[o:o + 2], "little")
            if 0x08002000 <= base + 2 * v <= 0x08031000:
                good += 1
        if good == 4:
            big = i
            break
    if big is None:
        print("  no tbh found"); continue
    # resolve the big table by reading a generous window and keeping entries
    # that land inside the firmware's handler region
    base = big.address + 4
    entries = []
    for k in range(0x40):
        o = big.address + 4 - FLASH_BASE + 2 * k
        v = int.from_bytes(code[o:o + 2], "little")
        tgt = base + 2 * v
        entries.append((k, v, tgt))
    print("  big tbh @%08x, base 0x%08x" % (big.address, base))
    lo = min(t for _, _, t in entries if 0x08002000 <= t <= 0x08031000)
    hi = max(t for _, _, t in entries if 0x08002000 <= t <= 0x08031000)
    print("  handler targets span 0x%08x .. 0x%08x" % (lo, hi))
    print()
    print("  k(idx-pivot)  raw   target")
    for k, v, tgt in entries[:0x24]:
        ok = "ok" if 0x08002000 <= tgt <= 0x08031000 else "?? (data/padding)"
        print("    %-3d %-5d 0x%08x  %s" % (k, v, tgt, ok))
    print()
