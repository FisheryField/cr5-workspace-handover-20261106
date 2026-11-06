#!/usr/bin/env python3
"""Callers via RAW Thumb-2 BL/BLX decoding - no decoder in the loop.

The capstone-operand approach returned 0 call sites for five functions in a
500,000-instruction sweep, which is impossible and is the 9th silent-empty
result of this investigation.  So the branch targets are now computed
arithmetically straight from the encoding, which cannot silently fail:

  BL   : 1111 0 S imm10  |  11 J1 1 J2 imm11
  BLX  : 1111 0 S imm10  |  11 J1 0 J2 imm11
  target = pc + 4 + SignExtend(S:J1:imm10:J2:imm11:0)

Positive control: the well-known calls INSIDE DataSubProcess::updateEncoderData
(0x000f9520..0x000f9c2c, e.g. `blx 0x000ba8fc` at 0x000f955c) must be found, and
a large number of distinct targets must appear.  If either fails the tool says
so instead of printing an empty table.
"""
import os
import struct
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"

TARGETS = {
    0x000F9520: "DataSubProcess::updateEncoderData",
    0x001D9E90: "robot_control::updateEncoderData",
    0x000E520C: "DataSubProcess::getEncoderValue",
    0x000FBF30: "DataSubProcess::readCurrentEncoder",
    0x000F0428: "DataSubProcess::caliHome",
    0x000FB704: "DataSubProcess::goHome",
}


def thumb_bl_target(pl, i, base):
    """Return (target, is_blx) for a Thumb-2 BL/BLX at file offset i, else None."""
    if i + 4 > len(pl):
        return None
    w1, w2 = struct.unpack_from("<HH", pl, i)
    if (w1 & 0xF800) != 0xF000:
        return None
    # bits 15..14 must be 11; bit 12 distinguishes BL (1) from BLX (0).
    # An earlier version tested (w2 & 0xD000) == 0xD000, which REQUIRES bit12=1
    # and therefore discarded every BLX - only 3477 of ~50k branches were seen
    # and the control (which relies on a BLX) failed.
    if (w2 & 0xC000) != 0xC000:
        return None
    S = (w1 >> 10) & 1
    imm10 = w1 & 0x3FF
    J1 = (w2 >> 13) & 1
    J2 = (w2 >> 11) & 1
    imm11 = w2 & 0x7FF
    i1 = (~(J1 ^ S)) & 1
    i2 = (~(J2 ^ S)) & 1
    imm32 = (S << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        imm32 -= 1 << 25
    pc = base + i + 4
    is_blx = ((w2 >> 12) & 1) == 0
    return pc + imm32, is_blx


def main():
    d = open(P, "rb").read()
    (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
     shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(shnum):
        f = struct.unpack_from(SH_FMT, d, shoff + i * shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], entsize=f[9]))
    shstr = secs[shstrndx]
    for s in secs:
        e = d[shstr["offset"] + s["name_off"]:]
        s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")

    funcs = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[secs[s["link"]]["offset"] if False else s["link"]]["offset"] \
            if False else secs[s["link"]]["offset"]
        for k in range(s["size"] // (s["entsize"] or 16)):
            off = s["offset"] + k * 16
            if off + 16 > len(d):
                break
            no, value, size, info, _o, _sh = struct.unpack_from(SYM_FMT, d, off)
            if no == 0 or (info & 0xF) != 2 or not size:
                continue
            e = d[strt + no:]
            funcs.append((value & ~1, size, e[:e.index(b"\0")].decode("ascii", "replace")))
    funcs.sort()

    def owner(a):
        best = None
        for ad, sz, nm in funcs:
            if ad > a:
                break
            if ad <= a < ad + sz:
                best = (ad, nm)
        return best

    text = next(s for s in secs if s["name"] == ".text")
    base = text["addr"]
    print(".text 0x%08x..0x%08x  %d bytes   (%d symbols)"
          % (base, base + text["size"], text["size"], len(funcs)))

    sites = defaultdict(list)
    n = 0
    for off in range(0, text["size"] - 4, 2):
        r = thumb_bl_target(d, text["offset"] + off, base)
        if r is None:
            continue
        t, is_blx = r
        sites[t & ~1].append(base + off)
        n += 1
    print("Thumb BL/BLX instructions found: %d   distinct targets: %d"
          % (n, len(sites)))

    # ---- positive control ----
    # NOTE: the control must look at the SITE address, not the target.  An
    # earlier version asked "is there a call whose TARGET lies inside
    # updateEncoderData", which is the wrong question - the calls inside it are
    # `blx` to PLT stubs at ~0x000bxxxx, so the control failed while the scanner
    # was actually fine.
    ctrl_lo, ctrl_hi = 0x000F9520, 0x000F9520 + 1804
    ctrl = [s for _t, ss in sites.items() for s in ss if ctrl_lo <= s < ctrl_hi]
    tmin = min(sites) if sites else 0
    tmax = max(sites) if sites else 0
    print("control: call SITES inside updateEncoderData = %d (expect several)" % len(ctrl))
    print("target range 0x%08x .. 0x%08x" % (tmin, tmax))
    ok = len(ctrl) >= 3 and n > 10000 and len(sites) > 3000
    print("controls: %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        print("!! aborting rather than printing an empty caller table")
        return 2

    print()
    print("=" * 84)
    print("CALLERS")
    print("=" * 84)
    for t, label in TARGETS.items():
        sz = next((z for a, z, nm in funcs if a == t), None)
        if sz is None:
            print("  %-40s @0x%08x : no symbol" % (label, t))
            continue
        hits = []
        for tt, ss in sites.items():
            if t <= tt < t + sz:
                for s in ss:
                    o = owner(s)
                    if o and o[0] != t:
                        hits.append((s, o))
        print("  %-40s @0x%08x : %d external call site(s)"
              % (label, t, len(hits)))
        for s, o in sorted(hits)[:25]:
            print("      call @0x%08x   in %s @0x%08x" % (s, o[1], o[0]))
        if len(hits) > 25:
            print("      ... %d more" % (len(hits) - 25))
    return 0


if __name__ == "__main__":
    sys.exit(main())
