#!/usr/bin/env python3
"""Generic Thumb disassembler for libalgs_framework.so.bin.

usage:  algs_dis.py <hexaddr> [nbytes] [--raw]
Resolves literal-pool loads (ldr rX,[pc,#imm]) so targets show up inline.
Positive control at import: disassembles the known PROLOGUE of
_Z18CheckAlarmAndResetj and asserts it decodes to >= 3 instructions.
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()

# PT_LOAD table (from pyelftools: segments are identity-mapped here for .text)
V2O = [(0x000000, 0x000000, 0x1aba08)]   # vaddr, foff, filesz  (RO+text)
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
md.detail = True


def v2o(a):
    for v, o, sz in V2O:
        if v <= a < v + sz:
            return o + (a - v)
    raise ValueError("no mapping for 0x%x" % a)


def litval(addr, insn):
    """If insn is ldr rX,[pc,#imm], return (regname, value) of the literal."""
    if not insn.operands or insn.mnemonic not in ("ldr", "ldr.w", "vldr"):
        return None
    ops = insn.operands
    if len(ops) < 2 or ops[1].type != ARM_OP_MEM:
        return None
    if ops[1].mem.base != ARM_REG_PC:
        return None
    pc = (insn.address + 4) & ~3
    tgt = pc + ops[1].mem.disp
    try:
        o = v2o(tgt)
    except ValueError:
        return None
    if insn.mnemonic == "vldr":
        return ("s%d" % ops[0].reg, struct.unpack_from("<I", DATA, o)[0], tgt)
    return (insn.reg_name(ops[0].reg), struct.unpack_from("<I", DATA, o)[0], tgt)


def dis(a, n, follow=True):
    a0 = a
    off = v2o(a)
    code = DATA[off:off + n]
    out = []
    for insn in md.disasm(code, a0 | 1 if False else a0):
        line = "0x%08x  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)
        if follow:
            lv = litval(insn.address, insn)
            if lv:
                reg, val, tg = lv
                extra = ""
                # try reading as a string
                try:
                    oo = v2o(val)
                    s = DATA[oo:oo + 40]
                    if s[:1].isalpha() or s[:1] == b"/":
                        z = s.split(b"\0")[0]
                        if len(z) >= 4 and all(32 <= c < 127 for c in z):
                            extra = "   ; \"%s\"" % z.decode()
                except ValueError:
                    pass
                line += "   ; [0x%08x]=0x%08x%s" % (tg, val, extra)
        out.append(line)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    a = int(sys.argv[1], 16)
    n = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x100
    raw = "--raw" in sys.argv
    print("# --- 0x%08x .. 0x%08x ---" % (a, a + n))
    for l in dis(a, n, follow=not raw):
        print(l)
    return 0


if __name__ == "__main__":
    # POSITIVE CONTROL
    ct = dis(0x198674, 0x20)
    assert len(ct) >= 3, "control failed"
    sys.exit(main())
