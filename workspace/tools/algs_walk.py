#!/usr/bin/env python3
"""Walk .text backwards to the nearest plausible function prologue, then
disassemble forward with capstone and report every call to a target.

usage: algs_walk.py <hexaddr_of_interest>
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x4C340, 0x4C340, 0x15F6BA
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True

PROLOGUES = {0xE92D, 0xB5F0, 0xB5F8, 0xB570, 0xB580, 0xB510, 0xB5B0, 0xB538}


def is_prologue(a):
    w1 = struct.unpack_from("<H", DATA, a)[0]
    if (w1 & 0xFF00) == 0xB500:      # push {..,lr}
        return True
    if w1 == 0xE92D:                 # push.w {..}
        return True
    return False


def main():
    want = int(sys.argv[1], 16)
    # find nearest prologue at or before want
    a = want & ~1
    start = None
    for probe in range(a, max(TEXT_VA, a - 0x3000), -2):
        if is_prologue(probe):
            start = probe
            break
    print("nearest prologue at or before 0x%08x: %s"
          % (want, hex(start) if start else "none"))
    if start is None:
        return 1
    end = min(start + 0x4000, TEXT_VA + TEXT_SZ)
    insns = list(MD.disasm(DATA[start:end], start))
    print("decoded %d insns from 0x%08x" % (len(insns), start))
    # report calls, plus everything within 0x200 of `want`
    for insn in insns:
        if insn.mnemonic in ("bl", "blx") and insn.operands \
                and insn.operands[0].type == ARM_OP_IMM:
            t = insn.operands[0].imm
            mark = "   <== TARGET" if (t & ~1) == (want & ~1) else ""
            if not mark and abs(insn.address - want) > 0x400:
                continue
            print("  0x%08x  %-4s 0x%08x%s" % (insn.address, insn.mnemonic, t, mark))
        elif abs(insn.address - want) <= 0x40:
            print("  0x%08x  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
