#!/usr/bin/env python3
"""Find EVERY TxPDO-like block run in a codesyscontrol dump (not just the first).

Motivation: the master's reported joint angle for J6 (115034.8 counts) does NOT
match the `0x6064` slot (-4) of the block run that tools/txpdo_decode.py finds
first - but it does match the LAST 32-bit slot (+67, = -115029).  So either

  (a) many copies of the per-slave process image exist and the one the PLC
      actually reads has J6's position somewhere else, or
  (b) the reported value is not taken from this image at all.

This tool enumerates all candidate runs so (a) can be checked directly.

Signature per run: version word 0x32D8 (J1..J5) / 0x3150 (J6) at the offsets
implied by the exact block sizes 57/57/57/93/69/71.
"""
import struct
import sys

SIZES = [57, 57, 57, 93, 69, 71]
# offset of 0x5000:07 inside each block (J1..J5: 35, J6: 37)
VWOFF = [35, 35, 35, 35, 35, 37]
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]


def main():
    path = sys.argv[1]
    base = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x73000000
    d = open(path, "rb").read()
    p32 = struct.pack("<H", 0x32D8)
    p50 = struct.pack("<H", 0x3150)

    # cumulative offsets of each block start relative to the J1 block start
    cum = [0]
    for s in SIZES[:-1]:
        cum.append(cum[-1] + s)

    runs = []
    cands = []
    a = 0
    while True:
        a = d.find(p32, a)
        if a < 0:
            break
        cands.append(a)
        a += 1                          # NOTE: must advance past the hit, not
                                        # to the candidate base (infinite loop)
    for a in cands:
        cand = a - VWOFF[0]             # candidate J1 block base
        if cand < 0:
            continue
        ok = True
        for k in range(6):
            off = cand + cum[k] + VWOFF[k]
            want = p50 if k == 5 else p32
            if off + 2 > len(d) or d[off:off + 2] != want:
                ok = False
                break
        if ok:
            runs.append(cand)

    print("dump %d bytes base 0x%08x ; candidate runs: %d" %
          (len(d), base, len(runs)))
    if not runs:
        print("!! no run found - do NOT conclude anything")
        return 2

    for r in runs:
        print()
        print("=" * 74)
        print("RUN @ %08x (dump+0x%x)" % (base + r, r))
        print("=" * 74)
        for k in range(6):
            b = r + cum[k]
            sz = SIZES[k]
            if b + sz > len(d):
                continue
            def i32(o):
                return struct.unpack_from("<i", d, b + o)[0]
            def i16(o):
                return struct.unpack_from("<h", d, b + o)[0]
            print("  %s base %08x  pos(+3)=%-10d status(+0)=%d  vw(+%d)=%d  "
                  "last32(+%d)=%d"
                  % (NAMES[k], base + b, i32(3), i16(0), VWOFF[k],
                     i16(VWOFF[k]), sz - 4, i32(sz - 4)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
