#!/usr/bin/env python3
"""Find callers with an ALIGNMENT FILTER: a candidate BL site is accepted only
if capstone, decoding a short window that starts a few bytes earlier, arrives
exactly at that site (i.e. the site is genuinely on an instruction boundary).

This works around the fact that linear decoding dies on padding, without
needing a hand-rolled BL decoder.

usage: algs_caller2.py <hex_target> [<hex_target> ...]
"""
import bisect
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


def on_boundary(a):
    """Is `a` an instruction boundary?  Try decoding short windows that start
    at a-2, a-4, a-6 ... inside the same function."""
    st, sz, nm = enclosing(a)
    lo = st if st is not None else a - 0x400
    for back in range(2, 34, 2):
        s = a - back
        if s < lo:
            break
        insns = list(MD.disasm(DATA[s:s + back + 4], s))
        if any(i.address == a for i in insns):
            return True, nm
    return False, nm


def main():
    # POSITIVE CONTROL: the known site 0x941f8 -> 0x940cc must pass the filter
    okc, _ = on_boundary(0x941F8)
    print("POSITIVE CONTROL 0x941f8 on instruction boundary: %s"
          % ("PASS" if okc else "FAIL"))
    assert okc

    for a in sys.argv[1:]:
        want = int(a, 16)
        # decoder-free candidate list: every word that looks like a Thumb-2
        # BL/BLX; capstone then decides what it really is.
        cands = []
        o = TEXT_OFF
        end = TEXT_OFF + TEXT_SZ - 4
        while o <= end:
            w1, w2 = struct.unpack_from("<HH", DATA, o)
            if (w1 & 0xF800) in (0xF000, 0xF800) and (w2 & 0xD000) == 0xD000:
                cands.append(TEXT_VA + (o - TEXT_OFF))
            o += 2
        good = []
        for c in cands:
            ok, nm = on_boundary(c)
            if not ok:
                continue
            insns = list(MD.disasm(DATA[c:c + 4], c))
            if not insns:
                continue
            insn = insns[0]
            if insn.mnemonic not in ("bl", "blx") or not insn.operands:
                continue
            if insn.operands[0].type != ARM_OP_IMM:
                continue
            if (insn.operands[0].imm & ~1) == (want & ~1):
                good.append((c, insn.mnemonic, nm))
        print()
        print("target 0x%08x: %d BL-shaped words, %d verified by capstone"
              % (want, len(cands), len(good)))
        seen = set()
        for c, mn, nm in good:
            if (nm, mn) in seen:
                continue
            seen.add((nm, mn))
            print("    site 0x%08x  %-4s in %s" % (c, mn, nm))
    return 0


if __name__ == "__main__":
    sys.exit(main())
