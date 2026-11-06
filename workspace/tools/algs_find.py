#!/usr/bin/env python3
"""Find symbols matching a regex, print exact value/size, and disassemble each
with capstone (from the symbol start, so the Thumb bit / alignment is right)."""
import re
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"


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
pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else ".")
want_dis = "--dis" in sys.argv
nmax = 40
shown = 0
seen = set()
for s in SYMS:
    if s["type"] != 2 or not pat.search(s["name"]):
        continue
    k = (s["name"], s["value"])
    if k in seen:
        continue
    seen.add(k)
    print("%-10s 0x%08x size=%-6d shndx=%-3d %s"
          % (s["tab"], s["value"], s["size"], s["shndx"], s["name"]))
    shown += 1
    if want_dis and s["size"] and s["shndx"] == 11:
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        insns = list(md.disasm(DATA[s["value"]:s["value"] + s["size"]], s["value"]))
        end = insns[-1].address + insns[-1].size if insns else s["value"]
        print("    # capstone decoded %d insns, reached 0x%08x of 0x%08x (%s)"
              % (len(insns), end, s["value"] + s["size"],
                 "FULL" if end == s["value"] + s["size"] else "PARTIAL"))
        for insn in insns:
            print("    %08x  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
    if shown >= nmax:
        break
print("# matches shown: %d" % shown)
