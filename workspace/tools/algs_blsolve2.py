#!/usr/bin/env python3
"""Exhaustively solve the Thumb-2 BL/BLX immediate layout on this binary.

Search space: which contiguous bit range of w1 is imm10, which contiguous bit
range of w2 is imm11, which two bits of w2 are J1/J2, which bit of w1 is S.
We accept a (layout, bias) only on 100% agreement with capstone ground truth.
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM

sys.path.insert(0, r"D:\mydata\workspace\tools")
import algs_blsweep as S                       # noqa: E402


def ground_truth(limit=250):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    out, used = [], 0
    for st, sz, nm in S.FUNCS:
        if used >= limit or sz == 0:
            continue
        insns = list(md.disasm(S.DATA[st:st + sz], st))
        if not insns or insns[-1].address + insns[-1].size != st + sz:
            continue
        used += 1
        for insn in insns:
            if insn.mnemonic not in ("bl", "blx"):
                continue
            if not insn.operands or insn.operands[0].type != ARM_OP_IMM:
                continue
            w1, w2 = struct.unpack_from("<HH", S.DATA, insn.address)
            out.append((insn.address, insn.operands[0].imm))
    return out, used


def field(word, start, length):
    return (word >> start) & ((1 << length) - 1)


def main():
    gt, used = ground_truth(250)
    print("ground truth: %d sites / %d functions" % (len(gt), used))

    solved = []
    for i10_pos in range(0, 7):
        for i10_len in (8, 9, 10, 11):
            for i11_pos in range(0, 6):
                for i11_len in (9, 10, 11, 12):
                    for j1 in range(8, 16):
                        for j2 in range(8, 16):
                            if j1 == j2:
                                continue
                            for sbit in (10, 11, 12, 13, 14, 15, 26):
                                for bias in (0x2000000,):
                                    ok = 0
                                    for a, t in gt:
                                        w1, w2 = struct.unpack_from(
                                            "<HH", S.DATA, a)
                                        Sv = (w1 >> sbit) & 1 if sbit < 16 \
                                            else (w1 >> 10) & 1
                                        a10 = field(w1, i10_pos, i10_len)
                                        J1 = (w2 >> j1) & 1
                                        J2 = (w2 >> j2) & 1
                                        a11 = field(w2, i11_pos, i11_len)
                                        I1 = (~(J1 ^ Sv)) & 1
                                        I2 = (~(J2 ^ Sv)) & 1
                                        v = (Sv << (1 + i10_len + 2 + i11_len - 1)) \
                                            | (a10 << (2 + i11_len)) \
                                            | (I1 << (1 + i11_len)) \
                                            | (I2 << i11_len) | a11
                                        v = (v - bias) & 0x1FFFFFF
                                        if (a + 4 + v) & ~3 == t & ~3:
                                            ok += 1
                                    if ok == len(gt):
                                        solved.append((i10_pos, i10_len,
                                                       i11_pos, i11_len,
                                                       j1, j2, sbit, bias))
                                        print("SOLVED: imm10=(%d,%d) imm11=(%d,%d)"
                                              " J1=%d J2=%d S=%d bias=0x%x"
                                              % (i10_pos, i10_len, i11_pos,
                                                 i11_len, j1, j2, sbit, bias))
    if not solved:
        print("no layout achieved 100% - reporting best partial")
    else:
        print("total solved layouts: %d" % len(solved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
