#!/usr/bin/env python3
"""Capstone-based scan for memory accesses at specific struct offsets.

For every plausible function prologue, decode with capstone and report every
memory operand whose displacement is in a wanted set, resolving which
instruction materialised the base when it is a simple `add.w rD, rB, #imm`.

usage: algs_offscan.py <hexoff> [<hexoff> ...] [--region A B]
"""
import bisect
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_OP_REG

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x4C340, 0x4C340, 0x15F6BA
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True


def load_syms():
    (_t, _m, _v, _e, _ph, e_shoff, _fl, _eh, _phes, _phn, e_shentsize,
     e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", DATA, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from(SH_FMT, DATA, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = DATA[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    out = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // 16 if s["entsize"] == 0 else s["size"] // s["entsize"]
        for i in range(n):
            off = s["offset"] + i * 16
            name_o, value, size, info, _o, shndx = struct.unpack_from(SYM_FMT, DATA, off)
            if name_o == 0:
                continue
            e = DATA[base + name_o:]
            name = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append((value & ~1, size, name, info & 0xF, shndx))
    return out


SY = load_syms()
ext = {}
for v, sz, nm, ty, sh in SY:
    if sh != 11 or ty != 2:
        continue
    if v not in ext or sz > ext[v][1]:
        ext[v] = (nm, sz)
FUNCS = sorted((v, sz, nm) for v, (nm, sz) in ext.items())
FS = [f[0] for f in FUNCS]


def enclosing(a):
    i = bisect.bisect_right(FS, a) - 1
    if i >= 0:
        return FUNCS[i]
    return (None, None, None)


def prologues(lo, hi):
    out = []
    for a in range(lo, hi - 4, 2):
        w1 = struct.unpack_from("<H", DATA, a)[0]
        if w1 == 0xE92D:
            w2 = struct.unpack_from("<H", DATA, a + 2)[0]
            if w2 & 0x4000:
                out.append(a)
        elif (w1 & 0xFF00) == 0xB500:
            out.append(a)
    return out


def main():
    argv = sys.argv[1:]
    offs = set()
    lo, hi = TEXT_VA, TEXT_VA + TEXT_SZ
    if "--region" in argv:
        k = argv.index("--region")
        lo, hi = int(argv[k + 1], 16), int(argv[k + 2], 16)
        del argv[k:k + 3]
    for x in argv:
        offs.add(int(x, 16))
    print("wanted displacements: %s" % ", ".join("0x%x" % o for o in sorted(offs)))
    print("region 0x%08x..0x%08x" % (lo, hi))

    bases = prologues(lo, min(hi, TEXT_VA + TEXT_SZ))
    print("prologues: %d" % len(bases))
    # POSITIVE CONTROL: 0x4b0 must be seen based off the `add.w sb,#0x4b0`
    seen_4b0 = False
    hits = []
    for st in bases:
        if st < lo or st >= hi:
            continue
        insns = list(MD.disasm(DATA[st:st + 0x4000], st))
        for insn in insns:
            if insn.address >= hi:
                break
            for op in insn.operands:
                if op.type != ARM_OP_MEM or op.mem.disp == 0:
                    continue
                if op.mem.base == 0 or insn.reg_name(op.mem.base) == "pc":
                    continue           # PC-relative literal load, not a field
                if op.mem.disp in offs:
                    if op.mem.disp == 0x4B0:
                        seen_4b0 = True
                    hits.append((insn.address, op.mem.disp, insn.mnemonic,
                                 insn.op_str, st))
    print("POSITIVE CONTROL offset 0x4b0 seen: %s" % ("PASS" if seen_4b0 else "FAIL"))
    print()
    seen = set()
    for a, d, mn, ops, st in sorted(hits):
        key = (st, d, a)
        if key in seen:
            continue
        seen.add(key)
        _s, _z, nm = enclosing(a)
        print("  0x%08x  +0x%-5x %-6s %-34s in %s" % (a, d, mn, ops, nm))
    print("total hits: %d" % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
