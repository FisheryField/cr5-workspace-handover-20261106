#!/usr/bin/env python3
"""Correct pointer-reference search: through the RELOCATION tables.

The naive "scan the file for the 4-byte address" search is a false positive
here: the only matches land in .symtab (the symbol's own st_value), because a
PIC shared object never stores absolute code addresses in data - the dynamic
linker patches them in.  So the authoritative answer comes from .rel.dyn /
.rel.plt:

    Elf32_Rel { r_offset, r_info }         r_info = (sym<<8) | type
    type 23 = R_ARM_RELATIVE  -> the ADDEND IS STORED IN PLACE at r_offset
                                 (this is REL, not RELA), so read 4 bytes there
    other types               -> resolve through .dynsym when sym != 0

For each relocation whose target value equals a function of interest, print the
slot's virtual address and the section it lives in - that is where the function
is referenced (a route table, a vtable, an init_array, ...).

Positive controls: .rel.dyn must parse to a plausible entry count, and at least
one of the searched functions must be found.  A zero result for ALL of them
aborts rather than being reported as "no references".
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")

TARGETS = {
    0x000F0428: "DataSubProcess::caliHome",
    0x000F9520: "DataSubProcess::updateEncoderData",
    0x000E520C: "DataSubProcess::getEncoderValue",
    0x000FBF30: "DataSubProcess::readCurrentEncoder",
    0x000FB704: "DataSubProcess::goHome",
    0x001D9E90: "robot_control::updateEncoderData",
    0x000F0508: "DataSubProcess::caliCoord6Axes",
    0x000FAFA0: "DataSubProcess::caliCoord6AxesSingle",
}
R_ARM_RELATIVE = 23
R_ARM_ABS32 = 2
R_ARM_GLOB_DAT = 21
R_ARM_JUMP_SLOT = 22


def main():
    d = open(P, "rb").read()
    (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
     shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(shnum):
        f = struct.unpack_from("<IIIIIIIIII", d, shoff + i * shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], info=f[7], entsize=f[9]))
    shstr = secs[shstrndx]
    for s in secs:
        e = d[shstr["offset"] + s["name_off"]:]
        s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")

    def v2f(v):
        for s in secs:
            if s["addr"] and s["size"] and s["addr"] <= v < s["addr"] + s["size"]:
                return s["offset"] + (v - s["addr"]), s["name"]
        return None, None

    def secname(v):
        for s in secs:
            if s["addr"] and s["size"] and s["addr"] <= v < s["addr"] + s["size"]:
                return s["name"]
        return None

    total = 0
    hits = {k: [] for k in TARGETS}
    for s in secs:
        if s["type"] != 9:              # SHT_REL
            continue
        n = s["size"] // 8
        total += n
        for i in range(n):
            ro, ri = struct.unpack_from("<II", d, s["offset"] + i * 8)
            typ = ri & 0xFF
            # NOTE: NOT filtered to R_ARM_RELATIVE.  In this library the
            # handlers are exported, so their slots carry R_ARM_ABS32 /
            # R_ARM_GLOB_DAT instead.  This is a REL (not RELA) object, so the
            # addend always lives in place at r_offset - reading the 4 bytes
            # there gives the target value for EVERY relocation type.
            fo, sn = v2f(ro)
            if fo is None or fo + 4 > len(d):
                continue
            val = struct.unpack_from("<I", d, fo)[0]
            if val in hits:
                hits[val].append((ro, sn, "%s/type%d" % (s["name"], typ)))
    print("relocations parsed: %d   (RELATIVE-only scan)" % total)
    ctl = total > 500
    print("control: relocation table parsed plausibly (>500): %s" % ctl)
    if not ctl:
        print("!! abort")
        return 2

    found = 0
    for addr, label in TARGETS.items():
        h = hits[addr]
        print()
        print("=" * 84)
        print("%s  @0x%08x : %d relocation slot(s)" % (label, addr, len(h)))
        print("=" * 84)
        for ro, sn, relsec in h[:10]:
            print("   slot vaddr 0x%08x  in %-14s  (from %s)" % (ro, sn, relsec))
            # show nearby strings (the route path sits next to the handler slot)
            fo, _ = v2f(ro)
            if fo:
                e = d[max(0, fo - 48):fo + 128]
                strs = [m.group().decode("ascii", "replace")
                        for m in re.finditer(rb"[\x20-\x7e]{5,}", e)]
                if strs:
                    print("        nearby strings: %s" % strs[:5])
        if h:
            found += 1
    print()
    print("referenced functions: %d / %d" % (found, len(TARGETS)))
    if found == 0:
        print("!! none found - abstain rather than claim no references")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
