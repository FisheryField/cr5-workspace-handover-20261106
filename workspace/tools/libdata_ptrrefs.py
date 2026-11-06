#!/usr/bin/env python3
"""Find POINTER references to a function - the right way to find its users.

Callers of caliHome / readCurrentEncoder / goHome are NOT `bl` sites: those are
HTTP handlers registered in a route table, and updateEncoderData is reached
through a periodic-task or vtable slot.  So the search is for the function's
ADDRESS materialised as 4 little-endian bytes anywhere in the file - which
covers route tables, vtables, literal pools and init arrays at once.

Also resolves the strings nearby, because a route table entry sits next to its
route path and that names the handler.

Positive control: the address of a function must be found at least once
otherwise nothing in the image could ever call it, so a zero result for every
target aborts instead of being reported as fact.
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
}


def main():
    d = open(P, "rb").read()
    # map file offset -> vaddr using the section headers
    (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
     shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(shnum):
        f = struct.unpack_from("<IIIIIIIIII", d, shoff + i * shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5]))
    shstr = secs[shstrndx]
    for s in secs:
        e = d[shstr["offset"] + s["name_off"]:]
        s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")

    def sec_of_vaddr(v):
        for s in secs:
            if s["addr"] and s["addr"] <= v < s["addr"] + s["size"]:
                return s["name"]
        return None

    def cstr_at(off, back=0, fwd=160):
        e = d[max(0, off - back):off + fwd]
        out = []
        for m in re.finditer(rb"[\x20-\x7e]{5,}", e):
            out.append(m.group().decode("ascii", "replace"))
        return out

    found_any = 0
    for addr, label in TARGETS.items():
        pat = struct.pack("<I", addr)
        hits = []
        i = d.find(pat)
        while i >= 0:
            hits.append(i)
            i = d.find(pat, i + 1)
        # which section is the pointer itself in?
        note = []
        for h in hits:
            sec = None
            for s in secs:
                if s["offset"] <= h < s["offset"] + s["size"] and s["size"]:
                    sec = s["name"]
                    break
            note.append((h, sec))
        print("=" * 84)
        print("%s  @0x%08x : %d pointer occurrence(s)" % (label, addr, len(hits)))
        print("=" * 84)
        for h, sec in note[:12]:
            print("  file 0x%06x  in %-14s   strings nearby: %s"
                  % (h, sec, cstr_at(h, 64, 96)[:4]))
        if hits:
            found_any += 1
        # also: 4-byte-aligned occurrences are the meaningful ones
        al = [h for h in hits if h % 4 == 0]
        print("  (4-byte aligned: %d)" % len(al))
    print()
    if found_any == 0:
        print("!! not a single function address found as data - abort/abstain")
        return 2
    print("found pointer tables for %d/%d functions" % (found_any, len(TARGETS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
