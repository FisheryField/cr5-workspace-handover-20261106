#!/usr/bin/env python3
"""PATCH FEASIBILITY CHECK (2/3): are the patch bytes branch targets?

If any BL/B/conditional branch (in EITHER build, since the code is shared shape)
lands inside the 4-byte instruction pair at 0x08014AFE..0x08014B02, then NOP-ing
it would break control flow and the patch is invalid.

Also checks the surrounding instruction boundaries so the replacement is known to
be exactly two 4-byte instructions (not one 4-byte + one 2-byte etc.).

Target patch site (3150 position chain):
    08014AFE  ldr  r1,=<0x20003DB0>
    08014B00  ldr  r1,[r1,#0x18]
    08014B02  add  r1,r0
    08014B04  str.w r1,[sb,#0x234]
"""
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

PATCH_LO = 0x08014AFE
PATCH_HI = 0x08014B04          # exclusive: instructions strictly below this

CASES = [("3150", "data/servo_fw_samples/elf/v3150.bin"),
         ("D8", "data/servo_fw_samples/elf/v328d8.bin")]


def decode_b_targets(insns):
    """Collect every branch target address in the image."""
    targets = {}
    for i in insns:
        m, o = i.mnemonic, i.op_str
        if not m.startswith("b") and m not in ("cbz", "cbnz"):
            continue
        # conditional + unconditional + cbz/cbnz -> '#0x...'
        if not o.startswith("#0x"):
            continue
        try:
            t = int(o[1:], 16)
        except ValueError:
            continue
        targets.setdefault(t, []).append((i.address, m, o))
    return targets


for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    byaddr = {i.address: i for i in insns}

    print("=" * 74)
    print("BUILD %s" % label)
    print("=" * 74)

    # instruction boundaries in the patch window
    print("  instructions in patch window 0x%08x..0x%08x:" % (PATCH_LO, PATCH_HI))
    for a in range(PATCH_LO, PATCH_HI, 2):
        i = byaddr.get(a)
        if i:
            print("    %08x  %-10s %-24s size=%d" % (a, i.mnemonic, i.op_str, i.size))

    tgt = decode_b_targets(insns)
    print()
    print("  total distinct branch targets in image: %d" % len(tgt))
    inside = [(t, v) for t, v in tgt.items() if PATCH_LO <= t < PATCH_HI]
    print("  branch targets INSIDE the patch window: %d" % len(inside))
    for t, v in inside:
        for a, m, o in v:
            print("    target 0x%08x  from %08x %-8s %s" % (t, a, m, o))

    # also: is the window reached as a fall-through from the previous insn?
    prev = byaddr.get(PATCH_LO - 2) or byaddr.get(PATCH_LO - 4)
    print()
    print("  preceding instruction: %s" % (("%08x %s %s" % (prev.address, prev.mnemonic, prev.op_str)) if prev else "?"))
    print()
