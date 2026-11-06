#!/usr/bin/env python3
"""Thumb BL/BLX call map built from .symtab function extents (reliable:
linear scan dies on inter-function padding).

POSITIVE CONTROL (assert / abort):
  * 0x198698 `bl` -> 0x196000 (AlarmSysSetBit)  - hand-read earlier
  * >= 10000 call sites total
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
V2O = [(0x0, 0x0, 0x1C95EC), (0x1DA000, 0x1CA000, 0x4034)]


def v2o(a):
    for v, o, sz in V2O:
        if v <= a < v + sz:
            return o + (a - v)
    return None


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
            out.append(dict(name=name, value=value & ~1, size=size,
                            type=info & 0xF, shndx=shndx, tab=s["name"]))
    return out


SYMS = load_syms()
# function extents: prefer .symtab, fall back to .dynsym; dedupe / merge
ext = {}
for s in SYMS:
    if s["shndx"] != 11 or s["type"] != 2 or s["size"] == 0:
        continue
    k = s["value"]
    if k not in ext or s["size"] > ext[k][1]:
        ext[k] = (s["name"], s["size"])
FUNCS = sorted((v, sz, nm) for v, (nm, sz) in ext.items())
FSTART = [f[0] for f in FUNCS]


def enclosing(a):
    i = bisect.bisect_right(FSTART, a) - 1
    if i >= 0:
        st, sz, nm = FUNCS[i]
        if st <= a < st + sz:
            return st, sz, nm
    return None, None, None


def build():
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    calls = []
    insns = 0
    bad = 0
    for st, sz, nm in FUNCS:
        o = v2o(st)
        if o is None:
            continue
        chunk = DATA[o:o + sz]
        got = 0
        for insn in md.disasm(chunk, st):
            got += 1
            insns += 1
            if insn.mnemonic in ("bl", "blx") and insn.operands \
                    and insn.operands[0].type == ARM_OP_IMM:
                calls.append((insn.address, insn.operands[0].imm, st, nm))
        if got * 2 < len(chunk):
            bad += 1
    return calls, insns, bad


def main():
    calls, insns, bad = build()
    print("functions with extents: %d" % len(FUNCS))
    print("instructions decoded: %d   partial-decode funcs: %d" % (insns, bad))
    print("BL/BLX sites: %d" % len(calls))
    pc1 = [c for c in calls if c[0] == 0x198698 and c[1] == 0x196000]
    print("POSITIVE CONTROL 1 (0x198698 -> AlarmSysSetBit 0x196000): %s"
          % ("PASS" if pc1 else "FAIL"))
    assert pc1, "control1"
    assert len(calls) > 10000, "control2"
    json.dump([[c[0], c[1], c[2], c[3]] for c in calls],
              open(r"D:\mydata\workspace\tools\algs_calls.json", "w"))

    print()
    print("=" * 78)
    print("callers of every AlarmSysSetBit clone")
    print("=" * 78)
    clones = sorted({(s["value"], s["name"]) for s in SYMS
                     if "AlarmSysSetBit" in s["name"] and s["type"] == 2
                     and s["tab"] == ".symtab"})
    for va, nm in clones:
        cs = [c for c in calls if c[1] == va]
        seen = []
        for ca, _t, cst, cnm in cs:
            if (cst, cnm) not in seen:
                seen.append((cst, cnm))
        print("  %-46s @0x%08x n=%d" % (nm, va, len(cs)))
        for cst, cnm in seen:
            print("      <- %s @0x%08x" % (cnm, cst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
