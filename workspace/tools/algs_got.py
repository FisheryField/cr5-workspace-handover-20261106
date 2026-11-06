#!/usr/bin/env python3
"""Resolve GOT slot offsets to symbol names using .rel.dyn + .dynsym.

The function under study uses the standard ARM PIC idiom
    ldr r7,[pc,#..] ; add r7,pc      -> r7 = base of .got
    ldr rX,[pc,#..] ; ldr rY,[r7,rX] -> rY = *(void**)(gotbase + MVA(instr))
so `MVA(instr)` (computed at 0x940de time) *is* the .got slot byte offset.
We map that offset to a relocation and therefore to a symbol name.

POSITIVE CONTROL: the slot 0x1774 / 0x186c etc. must resolve to *some*
relocation, and at least one of them must be a named OBJECT symbol.
"""
import struct
import sys

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"
GOTBASE = 0x1DBD08
GOT_SZ = 0x1AD4


def sections():
    (_t, _m, _v, _e, _ph, e_shoff, _fl, _eh, _phes, _phn, e_shentsize,
     e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", DATA, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from(SH_FMT, DATA, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], info=f[7], entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = DATA[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    return secs


SECS = sections()
BY_NAME = {s["name"]: s for s in SECS}


def dynsyms():
    s = BY_NAME[".dynsym"]
    strt = SECS[s["link"]]
    out = []
    n = s["size"] // 16
    for i in range(n):
        off = s["offset"] + i * 16
        name_o, value, size, info, _o, shndx = struct.unpack_from(SYM_FMT, DATA, off)
        if name_o == 0:
            out.append(None)
            continue
        e = DATA[strt["offset"] + name_o:]
        nm = e[:e.index(b"\0")].decode("ascii", "replace")
        out.append(dict(name=nm, value=value, size=size, type=info & 0xF,
                        shndx=shndx))
    return out


DSYMS = dynsyms()


def rel_dyn():
    s = BY_NAME[".rel.dyn"]
    n = s["size"] // 8
    out = []
    for i in range(n):
        r_off, r_info = struct.unpack_from("<II", DATA, s["offset"] + i * 8)
        out.append((r_off, r_info >> 8, r_info & 0xFF))
    return out


RELS = rel_dyn()
REL_BY_OFF = {o: (sym, typ) for o, sym, typ in RELS}


def resolve_slot(off):
    a = GOTBASE + off
    if a in REL_BY_OFF:
        si, typ = REL_BY_OFF[a]
        s = DSYMS[si] if si < len(DSYMS) else None
        return (s["name"] if s else "?", s["value"] if s else 0, typ)
    return None


def main():
    print("=" * 78)
    print("positive control: .rel.dyn must cover the GOT and name OBJECTs")
    print("=" * 78)
    print("  .rel.dyn entries: %d" % len(RELS))
    obj = [r for r in RELS if r[0] >= GOTBASE]
    print("  relocations inside .got (>=0x%08x): %d" % (GOTBASE, len(obj)))
    named = 0
    for o, si, typ in RELS:
        if o >= GOTBASE:
            s = DSYMS[si]
            if s and s["type"] == 1:
                named += 1
    print("  of which name an OBJECT symbol: %d" % named)
    assert obj, "control failed: no relocations in .got"

    print()
    print("=" * 78)
    print("slot offsets used by CheckErrorOfDemandAndNext (0x940cc)")
    print("=" * 78)
    for off in (0x1774, 0x186c, 0x15d4, 0x1614):
        r = resolve_slot(off)
        if r:
            print("  slot 0x%04x (addr 0x%08x): reloc type %d -> %s @0x%08x"
                  % (off, GOTBASE + off, r[2], r[0], r[1]))
        else:
            print("  slot 0x%04x (addr 0x%08x): NO relocation" % (off, GOTBASE + off))

    print()
    print("=" * 78)
    print("find the alarm-array slot: the setter does `ldr lr,[r8,r3]` with")
    print("r8 = .got+0x162c and r3 = 0x162c-style offset; list slots whose")
    print("target is a small (bitfield-sized) OBJECT near gAlarmSysState")
    print("=" * 78)
    for o, si, typ in RELS:
        if o < GOTBASE:
            continue
        s = DSYMS[si]
        if s and s["type"] == 1 and ("Alarm" in s["name"] or "alarm" in s["name"]):
            print("  slot 0x%04x -> %s @0x%08x size=%d"
                  % (o - GOTBASE, s["name"], s["value"], s["size"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
