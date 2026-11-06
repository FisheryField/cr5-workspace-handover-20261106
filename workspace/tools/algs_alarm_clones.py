#!/usr/bin/env python3
"""Dump all AlarmSysSetBit* symbol clones, hunt AlarmSysCheckAll, list
AlarmControl-region symbols.  ASCII only."""
import re
import struct
import sys

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
data = open(P, "rb").read()
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"
STT = {0: "NOTYPE", 1: "OBJECT", 2: "FUNC", 3: "SECTION", 4: "FILE",
       5: "COMMON", 6: "TLS", 10: "IFUNC"}


def load():
    (_t, _m, _v, _e, _ph, e_shoff, _fl, _eh, _phes, _phn, e_shentsize,
     e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", data, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from(SH_FMT, data, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                         offset=f[4], size=f[5], link=f[6], info=f[7],
                         entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = data[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    return secs


def symbols(secs):
    out = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // 16 if s["entsize"] == 0 else s["size"] // s["entsize"]
        for i in range(n):
            off = s["offset"] + i * 16
            name_o, value, size, info, _o, shndx = struct.unpack_from(SYM_FMT, data, off)
            if name_o == 0:
                continue
            e = data[base + name_o:]
            name = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append(dict(name=name, value=value, size=size,
                            type=STT.get(info & 0xF, "?"), bind=info >> 4,
                            shndx=shndx, tab=s["name"]))
    return out


secs = load()
syms = symbols(secs)

print("=" * 78)
print("A) every symbol whose name contains AlarmSysSetBit (all clones)")
print("=" * 78)
cl = sorted([s for s in syms if "AlarmSysSetBit" in s["name"] and s["type"] == "FUNC"],
            key=lambda s: s["value"])
for s in cl:
    print("  0x%08x size=%-6d %s" % (s["value"] & ~1, s["size"], s["name"]))
print("  FUNC clones: %d" % len(cl))

print()
print("=" * 78)
print("B) hunt AlarmSysCheckAll / CheckAll (symbol AND raw string)")
print("=" * 78)
for s in syms:
    if "CheckAll" in s["name"]:
        print("  SYM %-10s %-8s 0x%08x size=%-6d %s"
              % (s["tab"], s["type"], s["value"], s["size"], s["name"]))
for pat in [b"AlarmSysCheckAll", b"AlarmSysSetBit", b"alarms.h"]:
    print("  raw %-20s count=%d" % (pat.decode(), data.count(pat)))

print()
print("=" * 78)
print("C) symbols defined in alarms.cpp TU region + anything near AlarmControl")
print("=" * 78)
# .symtab entries with shndx==11 (.text)
txt = [s for s in syms if s["tab"] == ".symtab" and s["shndx"] == 11]
print("  .text FUNC syms: %d" % len(txt))
lo, hi = 0x196001, 0x1A64B1 + 12854
near = sorted([s for s in txt if lo - 0x2000 <= s["value"] <= hi + 0x4000],
              key=lambda s: s["value"])
for s in near[:400]:
    print("  0x%08x size=%-6d %s" % (s["value"] & ~1, s["size"], s["name"]))
print("  listed %d" % min(400, len(near)))
