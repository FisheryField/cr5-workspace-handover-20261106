#!/usr/bin/env python3
"""Enumerate every AlarmSysSetBit call inside a function range, with the
preceding instructions that set the argument register.

usage: algs_alarmsites.py <hexstart> <hexsize>
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
ALARMSETTERS = {0x9208C, 0x196000}
SETBIT_CLONES = {}
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True


def main():
    st = int(sys.argv[1], 16)
    sz = int(sys.argv[2], 16)
    insns = list(MD.disasm(DATA[st:st + sz], st))
    print("# %d insns in [0x%08x,0x%08x)" % (len(insns), st, st + sz))
    for i, insn in enumerate(insns):
        if insn.mnemonic != "bl" or not insn.operands:
            continue
        if insn.operands[0].type != ARM_OP_IMM:
            continue
        t = insn.operands[0].imm
        if t not in ALARMSETTERS:
            continue
        # back-scan for movs/mov r0,#imm
        arg = None
        ctx = []
        for j in range(max(0, i - 8), i + 1):
            k = insns[j]
            ctx.append("%08x %s %s" % (k.address, k.mnemonic, k.op_str))
            if k.mnemonic in ("movs", "mov", "mov.w") and k.op_str.startswith("r0, #"):
                try:
                    arg = int(k.op_str.split("#")[1], 0)
                except ValueError:
                    arg = None
        print("  site 0x%08x -> ALARM SETTER 0x%08x   index arg = %s"
              % (insn.address, t, hex(arg) if arg is not None else "?"))
        for c in ctx[-4:]:
            print("        %s" % c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
