#!/usr/bin/env python3
"""Solve the Thumb-2 BL immediate layout empirically against capstone.

Data: (a, target, w1, w2) for every `bl`/`blx` capstone reports inside a
function that decodes completely.  We then require, for 100% of the data,

    target == (a + 4 + off) & ~3
    off    == signedN(field) + BIAS

and search over plausible field layouts / BIAS values.
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM

sys.path.insert(0, r"D:\mydata\workspace\tools")
import algs_blsweep as S                       # noqa: E402


def ground_truth(limit=400):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    out = []
    used = 0
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
            out.append((insn.address, insn.operands[0].imm & ~3, w1, w2,
                        insn.mnemonic))
    return out, used


def assemble(w1, w2, s_bits, j_bits, imm10_pos, imm11_pos, imm11_len):
    def fld(w, pos):
        v = 0
        for bit in pos:
            v = (v << 1) | ((w >> bit) & 1)
        return v
    Sbit = fld(w1, s_bits)
    imm10 = fld(w1, imm10_pos)
    J = fld(w2, j_bits)
    imm11 = fld(w2, imm11_pos)
    v = (Sbit << (1 + len(imm10_pos) + len(j_bits) + imm11_len - 1)) | \
        (imm10 << (len(j_bits) + imm11_len)) | (J << imm11_len) | imm11
    return v


def main():
    gt, used = ground_truth(400)
    print("ground truth: %d BL sites from %d fully-decoded functions"
          % (len(gt), used))
    assert len(gt) > 200

    # derive required offset for each site
    req = [((t - (a + 4)) & 0xFFFFFFFF, a, t, w1, w2, m)
           for a, t, w1, w2, m in gt]
    # print a few raw requirements to see the low bits
    print("sample requirements (off_needed, w1, w2):")
    for off, a, t, w1, w2, m in req[:10]:
        print("   a=%08x t=%08x off=%08x w1=%04x w2=%04x" % (a, t, off, w1, w2))
    print()
    # Try: off is (assembled - 0x2000000) with canonical fields, then refine
    cands = []
    for s_bits in ([10], [10], [26], [26]):
        for imm10_pos in (list(range(0, 10)), list(range(10, 0, -1))):
            for j_bits in ([13, 11], [11, 13], [14, 12], [12, 14],
                           [15, 13], [13, 15], [13, 12], [12, 13]):
                for imm11_pos in (list(range(0, 11)), list(range(10, -1, -1))):
                    for bias in (0, 0x2000000):
                        ok = 0
                        for off, a, t, w1, w2, m in req:
                            v = assemble(w1, w2, s_bits, j_bits, imm10_pos,
                                         imm11_pos, 11)
                            v = (v - bias) & 0xFFFFFFFF
                            # interpret v as signed 26-bit
                            if v & 0x2000000:
                                v -= 0x4000000
                            if (a + 4 + v) & ~3 == t:
                                ok += 1
                        if ok > 0.5 * len(req):
                            cands.append((ok, tuple(s_bits), tuple(imm10_pos),
                                          tuple(j_bits), tuple(imm11_pos), bias))
    cands.sort(reverse=True)
    print("best layouts (ok/%d):" % len(req))
    for c in cands[:8]:
        print("   ok=%d S=%s imm10=%s J=%s imm11=%s bias=0x%x"
              % (c[0], c[1], c[2], c[3], c[4], c[5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
