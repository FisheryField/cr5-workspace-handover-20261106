#!/usr/bin/env python3
"""Validate the hand-rolled Thumb-2 BL decoder in algs_blsweep against capstone.

Every function whose whole extent capstone decodes end-to-end is used as
ground truth: each `bl`/`blx` immediate capstone reports is compared with
decode_bl() on the same bytes.  Reports agreement statistics and prints any
mismatching example.  This is the positive control that licenses the
brute-force sweep (which is needed because linear decode dies on padding).
"""
import struct
import sys

sys.path.insert(0, r"D:\mydata\workspace\tools")
import algs_blsweep as M                      # noqa: E402

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM


def main():
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    ok = bad = full_funcs = 0
    examples = []
    for st, sz, nm in M.FUNCS:
        o = M.v2o(st) if hasattr(M, "v2o") else None
        if o is None:
            o = st      # identity mapping in the first PT_LOAD
        chunk = M.DATA[o:o + sz]
        insns = list(md.disasm(chunk, st))
        # only trust functions decoded to the very end (no padding inside)
        if not insns:
            continue
        end = insns[-1].address + insns[-1].size
        if end != st + sz:
            continue
        full_funcs += 1
        for insn in insns:
            if insn.mnemonic not in ("bl", "blx"):
                continue
            if not insn.operands or insn.operands[0].type != ARM_OP_IMM:
                continue
            ct = insn.operands[0].imm
            w1, w2 = struct.unpack_from("<HH", M.DATA, insn.address)
            mine = M.decode_bl(insn.address, w1, w2)
            if (w2 & 0x1000):          # BLX targets are word aligned
                mine &= ~3
            if mine == ct or mine == (ct & ~1):
                ok += 1
            else:
                bad += 1
                if len(examples) < 6:
                    examples.append((insn.address, ct, mine))
    print("fully-decoded functions used as ground truth: %d" % full_funcs)
    print("BL/BLX immediate target agreement: ok=%d  mismatch=%d" % (ok, bad))
    for a, ct, mine in examples:
        print("  MISMATCH @0x%08x capstone=0x%08x mine=0x%08x" % (a, ct, mine))
    if ok == 0:
        print("!! no ground truth at all - validation inconclusive")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
