#!/usr/bin/env python3
"""Prologue-seeded call map: for every plausible Thumb function prologue in
.text, decode forward with capstone and record call targets.

Why: linear decoding dies at literal-pool padding, so a single sweep misses
sites; seeding at every prologue recovers them.

POSITIVE CONTROL: the map must contain 0x941f8 -> 0x9208c (hand-verified).
"""
import bisect
import json
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM

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


def prologues():
    out = []
    for a in range(TEXT_VA, TEXT_VA + TEXT_SZ - 4, 2):
        w1 = struct.unpack_from("<H", DATA, a)[0]
        if w1 == 0xE92D:                           # push.w {...,lr}
            w2 = struct.unpack_from("<H", DATA, a + 2)[0]
            if w2 & 0x4000:                        # lr in the register list
                out.append(a)
        elif (w1 & 0xFF00) == 0xB500:              # push {...lr}
            out.append(a)
    return out


def main():
    pro = prologues()
    print("prologue candidates: %d" % len(pro))
    calls = []
    for st in pro:
        insns = list(MD.disasm(DATA[st:st + 0x3000], st))
        for insn in insns:
            if insn.mnemonic in ("bl", "blx") and insn.operands \
                    and insn.operands[0].type == ARM_OP_IMM:
                calls.append((insn.address, insn.operands[0].imm,
                              insn.mnemonic))
    calls = sorted(set(calls))
    print("call sites: %d" % len(calls))
    ctl = [c for c in calls if c[0] == 0x941F8 and (c[1] & ~1) == 0x9208C]
    print("POSITIVE CONTROL 0x941f8 -> 0x9208c: %s"
          % ("PASS" if ctl else "FAIL"))
    assert ctl, "control failed"
    json.dump(calls, open(r"D:\mydata\workspace\tools\algs_calls2.json", "w"))

    print()
    for want in [int(x, 16) for x in sys.argv[1:]]:
        h = [c for c in calls if (c[1] & ~1) == (want & ~1)]
        seen = []
        for a, t, m in h:
            st, sz, nm = enclosing(a)
            if (st, nm) not in seen:
                seen.append((st, nm))
        print("target 0x%08x: %d sites, %d functions" % (want, len(h), len(seen)))
        for st, nm in seen:
            print("    %s @0x%08x" % (nm, st))
        for a, t, m in h[:20]:
            print("      site 0x%08x %s" % (a, m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
