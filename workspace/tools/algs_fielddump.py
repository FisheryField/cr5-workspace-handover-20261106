#!/usr/bin/env python3
"""Dump every instruction in a function that materialises a 32-bit value or
adds a constant to a register, plus all memory accesses with a big
displacement.  Used to find writers of gSR6Params+0x4b0 etc.

usage: algs_fielddump.py <hexstart> <hexsize> [imm ...]
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_OP_REG

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True


def main():
    st = int(sys.argv[1], 16)
    sz = int(sys.argv[2], 16)
    imms = {int(x, 16) for x in sys.argv[3:]} or None
    insns = list(MD.disasm(DATA[st:st + sz], st))
    print("# %d insns [0x%08x,0x%08x)" % (len(insns), st, st + sz))
    for k, insn in enumerate(insns):
        keep = False
        why = ""
        # immediate operand matching
        for op in insn.operands:
            if op.type == ARM_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                if imms is None:
                    if v >= 0x100:
                        keep, why = True, "imm 0x%x" % v
                elif v in imms:
                    keep, why = True, "imm 0x%x" % v
            if op.type == ARM_OP_MEM and op.mem.disp and \
                    insn.reg_name(op.mem.base) != "pc":
                if op.mem.disp >= 0x200:
                    keep, why = True, "disp 0x%x" % op.mem.disp
        if keep:
            print("  0x%08x  %-8s %-40s ; %s"
                  % (insn.address, insn.mnemonic, insn.op_str, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
