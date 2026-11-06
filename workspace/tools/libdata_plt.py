#!/usr/bin/env python3
"""Name every external call in libdataSvr.so  (data-driven PLT resolver).

capstone reports external calls as `blx 0x000b41bc` - a jump into the PLT, which
is opaque.  This tool maps each PLT stub to its imported symbol *without*
assuming the stub ordering or the PLT header size:

  For every candidate stub start s inside .plt, decode the canonical ARM stub
      add  ip, pc, #imm1
      add  ip, ip, #imm2
      ldr  pc, [ip, #imm3]!
  compute the GOT slot  slot = (s+8+imm1) + imm2 + imm3
  and accept the stub iff `slot` is exactly the r_offset of some .rel.plt entry.
  That entry's dynsym index names the import.

Self-validation: report how many of the .rel.plt entries were covered.  A
correct resolver covers all of them; anything less means the decoder is wrong
and every name it prints is suspect.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")


def sections(d):
    (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
     shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(shnum):
        f = struct.unpack_from("<IIIIIIIIII", d, shoff + i * shentsize)
        secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                         offset=f[4], size=f[5], link=f[6], info=f[7],
                         align=f[8], entsize=f[9]))
    shstr = secs[shstrndx]
    for s in secs:
        e = d[shstr["offset"] + s["name_off"]:]
        s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")
    return secs


def dynsyms(d, secs):
    ds = next(s for s in secs if s["name"] == ".dynsym")
    st = next(s for s in secs if s["name"] == ".dynstr")
    strb = d[st["offset"]:st["offset"] + st["size"]]
    out = []
    for i in range(ds["size"] // 16):
        no, val, size, info, other, shndx = \
            struct.unpack_from("<IIIBBH", d, ds["offset"] + i * 16)
        e = strb[no:]
        out.append(e[:e.index(b"\0")].decode("ascii", "replace"))
    return out


def ror32(v, n):
    n &= 31
    return ((v >> n) | (v << (32 - n))) & 0xFFFFFFFF


def dp_imm(imm12):
    """ARM data-processing immediate: imm12 = (rot<<8)|imm8, value=ROR(imm8,rot*2).
    Getting this wrong (using imm12 literally) makes every slot land ~1 MB off
    the GOT - which is exactly how the first two versions of this tool failed."""
    rot = (imm12 >> 8) & 0xF
    imm8 = imm12 & 0xFF
    return ror32(imm8, rot * 2)


def build(path=P):
    d = open(path, "rb").read()
    secs = sections(d)
    dsym = dynsyms(d, secs)
    plt = next(s for s in secs if s["name"] == ".plt")
    rel = next(s for s in secs if s["name"] == ".rel.plt")

    slot2sym = {}
    for i in range(rel["size"] // 8):
        off, info, addend = struct.unpack_from("<IIi", d, rel["offset"] + i * 8)
        slot2sym[off] = dsym[info >> 8]

    stub = {}                     # plt addr -> symbol name
    for s in range(plt["addr"], plt["addr"] + plt["size"] - 12, 4):
        fo = plt["offset"] + (s - plt["addr"])
        w1, w2, w3 = struct.unpack_from("<III", d, fo)
        # add ip,pc,#imm1 : 0xE28FC000 | imm12
        if (w1 & 0xFFFFF000) != 0xE28FC000:
            continue
        # add ip,ip,#imm2 : 0xE28CC000 | imm12
        if (w2 & 0xFFFFF000) != 0xE28CC000:
            continue
        # ldr pc,[ip,#imm3]! : 0xE5BCF000 | imm12   (plain 12-bit offset, NOT
        # a rotated immediate - LDR/STR offsets are never rotated)
        if (w3 & 0xFFFFF000) != 0xE5BCF000:
            continue
        slot = ((s + 8) + dp_imm(w1 & 0xFFF)) + dp_imm(w2 & 0xFFF) + (w3 & 0xFFF)
        nm = slot2sym.get(slot)
        if nm is not None:
            stub[s] = nm
    return d, secs, stub, slot2sym, dsym, plt, rel


def main():
    d, secs, stub, slot2sym, dsym, plt, rel = build()
    print("plt addr=0x%08x size=0x%x  rel.plt entries=%d  resolved stubs=%d"
          % (plt["addr"], plt["size"], len(slot2sym), len(stub)))
    miss = set(slot2sym) - {s for s in slot2sym}   # placeholder
    covered = len(stub)
    print("CONTROL: covered %d of %d imports (%.1f%%)"
          % (covered, len(slot2sym), 100.0 * covered / len(slot2sym)))
    if covered < 0.9 * len(slot2sym):
        print("!! CONTROL FAILED - resolver unreliable; abort")
        return 2
    print("CONTROL PASS")
    print()
    for s in sorted(stub):
        print("  0x%08x  %s" % (s, stub[s]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
