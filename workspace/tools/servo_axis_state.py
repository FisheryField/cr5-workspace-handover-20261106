#!/usr/bin/env python3
"""Differential scan of the two "axis state" structs.

CRITICAL CORRECTION this script encodes: the periodic per-axis position function
(D8 0x08010E60) uses TWO different structures:

    r5 = 0x2000138C + axis*0x329   <- descriptor array (OD field storage)
    r4 = arg1 (2nd function argument) <- AXIS RUNTIME STATE struct

and the position-loop working fields live on r4, NOT on r5:
    +0x14 reference position, +0x1C deviation, +0x20 step,
    +0x30 target position, +0x36 reinit latch, +0x24 corrected step
whereas r5 carries:
    +0x1AF position actual, +0x230 reference, +0x234 intermediate, +0x238 actual

So a scan keyed on the descriptor base literal finds *none* of the working fields,
which is exactly why the previous census returned all zeros.

This script therefore tracks the run-time struct by ONE OFFSET PROVENANCE:
  - follow `mov rX, rN` copies
  - follow `add/sub rX, rN, #imm` with an unknown base -> tag ('V', delta)
  - report accesses whose tag delta equals the field offset
That is enough to find e.g. `r4+0x14` sites and compare them across builds.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

FIELDS = [0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x36, 0x3C]

WRITE = ("str", "strb", "strh", "vstr", "strd")
READ = ("ldr", "ldrb", "ldrh", "vldr", "ldrsh", "ldrsb")


def scan(path):
    """Return {field: {'arith': [...], 'direct': [...]}} for the runtime struct.

    'arith'  = accesses of the form [rB,#off] where rB was produced by an
               `add/sub rB, rA, #imm` (i.e. a pointer to a sub-object)
    'direct' = plain [rB,#off] on any non-sp register -- kept separately because
               it is noisy, but useful when cross-checked with the function set.
    """
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    out = {f: [] for f in FIELDS}

    # find `add rB, rA, #imm` then a memory access [rB, #field]
    for k, i in enumerate(insns):
        if i.mnemonic not in ("add", "adds", "add.w", "addw"):
            continue
        mm = re.search(r"#(0x[0-9a-f]+)$", i.op_str)
        if not mm:
            continue
        dst = i.op_str.split(",")[0].strip()
        for j in range(k + 1, min(len(insns), k + 4)):
            x = insns[j]
            if "[" not in x.op_str or "pc" in x.op_str or "sp" in x.op_str:
                continue
            if not x.op_str.split("[", 1)[1].startswith(dst):
                continue
            fm = re.search(r"#(0x[0-9a-f]+)\]", x.op_str)
            if not fm:
                continue
            off = int(fm.group(1), 16)
            if off in out:
                out[off].append((x.address, x.mnemonic, x.op_str, i.address, i.op_str))
    return out


A = scan(CASES[0][1])
B = scan(CASES[1][1])

for f in FIELDS:
    print("+0x%02x : D8=%d  3150=%d" % (f, len(A[f]), len(B[f])))
    if len(A[f]) != len(B[f]):
        print("   <<< count differs")
    for a, m, o, pa, po in A[f][:4]:
        print("     D8   %08x %-9s %-22s  (base built @%08x %s)" % (a, m, o, pa, po))
    for a, m, o, pa, po in B[f][:4]:
        print("     3150 %08x %-9s %-22s  (base built @%08x %s)" % (a, m, o, pa, po))
