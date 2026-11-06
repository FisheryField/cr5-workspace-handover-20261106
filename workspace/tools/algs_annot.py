#!/usr/bin/env python3
"""Annotate a function: show every PC-relative load with its resolved MVA
(materialised value address), decode MVA -> GOT-relative global where the
pattern `add rX,pc` + `ldr rY,[rX,rZ]` appears, and dump literal-pool values
as ASCII strings when printable.

usage: algs_annot.py <hexstart> <hexsize>
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
SZ = len(DATA)


def rd(a, n):
    if a < 0 or a + n > SZ:
        return None
    return DATA[a:a + n]


def as_str(a, n=64):
    b = rd(a, n)
    if not b:
        return None
    z = b.split(b"\0")[0]
    if len(z) >= 4 and all(32 <= c < 127 for c in z):
        return z.decode()
    return None


def main():
    st = int(sys.argv[1], 16)
    sz = int(sys.argv[2], 16)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    insns = list(md.disasm(DATA[st:st + sz], st))
    print("# decoded %d insns (0x%x bytes requested)" % (len(insns), sz))
    pend = {}      # reg -> address materialised by add reg,pc
    for insn in insns:
        note = ""
        ops = insn.operands
        # ldr rX,[pc,#imm]  -> literal
        if insn.mnemonic in ("ldr", "ldr.w") and len(ops) == 2 \
                and ops[1].type == 3 and insn.reg_name(ops[1].mem.base) == "pc":
            pc = (insn.address + 4) & ~3
            lit = pc + ops[1].mem.disp
            v = rd(lit, 4)
            if v:
                val = struct.unpack("<I", v)[0]
                s = as_str(val)
                note = "; lit@0x%08x = 0x%08x%s" % (lit, val,
                                                   (' "%s"' % s) if s else "")
                if not s:
                    d = rd(val, 16)
                    note += " data=%s" % (d.hex(" ") if d else "-")
                pend["__lit_%s" % insn.reg_name(ops[0].reg)] = val
        # add rX, pc  -> MVA
        if insn.mnemonic.startswith("add") and len(ops) == 2 \
                and insn.reg_name(ops[1].reg) == "pc":
            key = "__lit_%s" % insn.reg_name(ops[0].reg)
            if key in pend:
                pc = insn.address + 4
                mva = pc + pend[key]
                pend[insn.reg_name(ops[0].reg)] = mva
                s = as_str(mva)
                note = "; MVA = pc+0x%x = 0x%08x%s" % (pend[key], mva,
                                                       (' "%s"' % s) if s else "")
        # add rX, rX, #imm  (add.w rX,rX,#k) -> adjust MVA
        if insn.mnemonic.startswith("add") and len(ops) == 3 \
                and ops[1].type == 1 and ops[2].type == 2:
            r = insn.reg_name(ops[1].reg)
            if r in pend and r not in ("sp",):
                pend[r] = (pend[r] + ops[2].imm) & 0xFFFFFFFF
                s = as_str(pend[r])
                note = "; MVA+0x%x -> 0x%08x%s" % (ops[2].imm, pend[r],
                                                   (' "%s"' % s) if s else "")
        if insn.mnemonic in ("addw",) and len(ops) == 3 and ops[1].type == 1:
            r = insn.reg_name(ops[1].reg)
            if r in pend:
                pend[r] = (pend[r] + ops[2].imm) & 0xFFFFFFFF
                s = as_str(pend[r])
                note = "; MVA+0x%x -> 0x%08x%s" % (ops[2].imm, pend[r],
                                                   (' "%s"' % s) if s else "")
        print("%08x  %-8s %-28s %s" % (insn.address, insn.mnemonic,
                                       insn.op_str, note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
