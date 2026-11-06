#!/usr/bin/env python3
"""Find the exact Thumb-2 BL/BLX immediate bit layout for this binary by
searching over halfword bit-fields and testing against capstone ground truth.

For each candidate layout we require: target == (insn_addr + 4 + off) with
off = signed(assembled_field) and the site set taken from capstone on
fully-decoded functions.  A layout is accepted only on 100% agreement.
"""
import struct
import sys

sys.path.insert(0, r"D:\mydata\workspace\tools")
import algs_blsweep as M                       # noqa: E402
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM


def ground_truth(limit_funcs=200):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    out = []
    used = 0
    for st, sz, nm in M.FUNCS:
        if used >= limit_funcs:
            break
        chunk = M.DATA[st:st + sz]
        insns = list(md.disasm(chunk, st))
        if not insns:
            continue
        if insns[-1].address + insns[-1].size != st + sz:
            continue
        used += 1
        for insn in insns:
            if insn.mnemonic not in ("bl", "blx"):
                continue
            if not insn.operands or insn.operands[0].type != ARM_OP_IMM:
                continue
            w1, w2 = struct.unpack_from("<HH", M.DATA, insn.address)
            out.append((insn.address, insn.operands[0].imm & ~1, w1, w2))
    return out, used


def field(word, start, length):
    return (word >> start) & ((1 << length) - 1)


def try_layout(gt, s1_bits, s2_bits, bias, signbit):
    """s1_bits: list of (start,length) from w1 low->high; s2_bits likewise."""
    ok = 0
    for a, t, w1, w2 in gt:
        off = 0
        shift = 0
        for st, ln in s1_bits + s2_bits:
            src = w1 if (st, ln) in s1_bits else w2
            off |= field(src, st, ln) << shift
            shift += ln
        if off & (1 << signbit):
            off -= (1 << (signbit + 1))
        if (a + 4 + off + bias) & ~1 == t or (a + 4 + off) & ~1 == t:
            ok += 1
    return ok


def main():
    gt, used = ground_truth(150)
    print("ground-truth BL sites from %d fully-decoded functions: %d"
          % (used, len(gt)))
    assert len(gt) > 100, "not enough ground truth"

    # canonical encoding: S(10,1) imm10(0,10) J1(13,1) J2(11,1) imm11(0,11)
    layouts = {
        "canon(lo->hi:S,imm10,J2,J1,imm11)": (
            [(10, 1), (0, 10)], [(11, 1), (13, 1), (0, 11)], 0, 24),
        "+0x2000000 bias": (
            [(10, 1), (0, 10)], [(11, 1), (13, 1), (0, 11)], 0x2000000, 24),
        "-0x2000000 bias": (
            [(10, 1), (0, 10)], [(11, 1), (13, 1), (0, 11)], -0x2000000, 24),
    }
    for name, (s1, s2, bias, sb) in layouts.items():
        ok = try_layout(gt, s1, s2, bias, sb)
        print("  %-40s ok=%d/%d" % (name, ok, len(gt)))

    # brute force over plausible field sets with a constant bias applied to
    # the *lowest* bit position handled separately
    print()
    print("brute force: S at bit b, imm10 at (0,10), J bits, imm11 at (0,11)")
    best = []
    for js1 in range(8, 16):
        for js2 in range(8, 16):
            for bias in (0, 0x2000000, -0x2000000):
                ok = try_layout(gt, [(10, 1), (0, 10)],
                                [(js1, 1), (js2, 1), (0, 11)], bias, 24)
                if ok > 0.9 * len(gt):
                    best.append((ok, js1, js2, bias))
    best.sort(reverse=True)
    for ok, js1, js2, bias in best[:10]:
        print("   ok=%d/%d J1bit=%d J2bit=%d bias=0x%x"
              % (ok, len(gt), js1, js2, bias))
    return 0


if __name__ == "__main__":
    sys.exit(main())
