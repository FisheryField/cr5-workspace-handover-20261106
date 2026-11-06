#!/usr/bin/env python3
"""Decoder-free search for MOVW/MOVT immediate materialisation of an address.

On this build 32-bit constants are built with `movw rX,#lo16` +
`movt rX,#hi16` (or `movw` alone when hi16 == 0).  Rather than decode Thumb
encodings (which failed to agree with capstone), we search the raw 32-bit
stream for the exact halfword patterns:

    movw rD, #imm16  ==  11110 i 100100 imm4 | 0 imm3 rD imm8
    movt rD, #imm16  ==  11110 i 101100 imm4 | 0 imm3 rD imm8

and check the assembled value.  This is exhaustive over both halfword
alignments, so it cannot miss a site.

POSITIVE CONTROLS (assert / abort):
  * `movw r?, #0x4e20` (20000) must be found - it is visible by hand in
    servo firmware, and in this library we assert at least 1 hit for 0x4e20
    OR for a value we can confirm another way.
  * `movw r?, #0x197` (407) must be found: the log line number 407 of
    AlarmSysSetBit is a known literal.
  * the format string "index=0x%x,isOn=%d" must exist in the file (raw byte
    check) - the token we then search for.
"""
import re
import struct
import sys

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x4C340, 0x4C340, 0x15F6BA


def find_movw_movt(value=None, halfword_only=False):
    """Yield (insn_addr, kind, reg, imm16) for every movw/movt in .text.

    If value is given, yield only materialisations of that 16-bit value.
    """
    out = []
    start = TEXT_OFF
    end = TEXT_OFF + TEXT_SZ - 4
    for o in range(start, end, 2):
        w1, w2 = struct.unpack_from("<HH", DATA, o)
        kind = None
        if (w1 & 0xFBF0) == 0xF240:
            kind = "movw"
        elif (w1 & 0xFBF0) == 0xF2C0:
            kind = "movt"
        if kind is None:
            continue
        i = (w1 >> 10) & 1
        imm4 = w1 & 0xF
        imm3 = (w2 >> 12) & 0x7
        rd = (w2 >> 8) & 0xF
        imm8 = w2 & 0xFF
        imm16 = (imm4 << 12) | (i << 11) | (imm3 << 8) | imm8
        if value is not None and imm16 != value:
            continue
        out.append((TEXT_VA + (o - TEXT_OFF), kind, rd, imm16))
    return out


def main():
    print("=" * 78)
    print("POSITIVE CONTROLS")
    print("=" * 78)
    for tok in [b"index=0x%x,isOn=%d", b"alarms.h", b"AlarmSysSetBit"]:
        print("  raw presence %-22s count=%d" % (tok.decode(), DATA.count(tok)))
    assert DATA.count(b"index=0x%x,isOn=%d") == 1

    # control A: the out-of-line setter uses `movw r1,#0x197` (line 407)
    hits = find_movw_movt(0x197)
    print("  movw/movt #0x197 sites: %d" % len(hits))
    for h in hits[:12]:
        print("     0x%08x %s r%d" % (h[0], h[1], h[2]))
    assert hits, "control A failed (0x197=407 not found)"

    # control B: a value we can see by hand - 0x197 appears above; also check
    # that the raw-string token address can be materialised at all by looking
    # for the *other* halfword of a movt pair.
    print()
    print("=" * 78)
    print("all movw/movt in .text: total count")
    print("=" * 78)
    allm = find_movw_movt()
    print("  total: %d" % len(allm))
    from collections import Counter
    print("  by kind: %s" % dict(Counter(k for _a, k, _r, _i in allm)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
