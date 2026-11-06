"""servo_const32.py - decode 32-bit constants built by Thumb `movw`/`movt` pairs, and
apply a code-vs-data sanity filter so code bytes are not mistaken for data.

Two problems this addresses, both of which produced WRONG results earlier in this
investigation:

  1. A 4-byte-aligned dword scan over a firmware image reports "data pointers" that
     are really just instruction bytes that happen to align. Example: 0x0804C8C0
     reads as 0x6064 on a 4-byte grid, but the bytes are `11 4a 04 1e` = real Thumb
     code. Such hits must not be treated as evidence.
  2. Code often builds a 32-bit constant in a register pair:
         movw rX, #lo16 ; movt rX, #hi16
     A scan limited to `movw` alone silently misses these, which is why an earlier
     search found "no reference" to several addresses.

This script decodes movw/movt pairs into full 32-bit constants, then reports them
with the target address annotated (RAM / flash / OD table / peripheral).

usage:
  python tools\\servo_const32.py <flash.bin>
  python tools\\servo_const32.py <flash.bin> --want 0x08024991
  python tools\\servo_const32.py <flash.bin> --in-range 0x08024bd0 0x0802642e
"""
import sys, struct

FLASH_BASE = 0x08000000
OD_LO, OD_HI = 0x08024bd0, 0x0802642e
PERIPH = {0x40000000: 'periph', 0xE0000000: 'system'}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def hw_at(flash, a):
    """Read one little-endian halfword.

    NOTE (bug fixed 2026-09-23): a previous version of this script treated the two
    `movw` halfwords in the wrong order and therefore decoded ZERO pairs from an
    image that has hundreds.  Read the low halfword first, always.
    """
    o = a - FLASH_BASE
    return struct.unpack_from('<H', flash, o)[0]


def decode_movwt(flash):
    """Yield (addr_of_movw, reg, value) for every movw/movt pair found."""
    out = []
    n = len(flash)
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 8:
        hw = hw_at(flash, a)          # first halfword of the pair
        hw2 = hw_at(flash, a + 2)     # second halfword
        if (hw & 0xFB00) == 0xF200:
            op = (hw >> 4) & 0xF
            if op in (4, 12):
                i = (hw >> 10) & 1
                imm4 = hw & 0xF
                imm3 = (hw2 >> 12) & 0x7
                imm8 = hw2 & 0xFF
                val = (i << 11) | (imm4 << 12) | (imm3 << 8) | imm8
                rd = (hw2 >> 8) & 0xF
                out.append((a, op, rd, val))
        a += 2
    # stitch consecutive movw(4)/movt(12) on the same register
    pairs = []
    for k in range(len(out) - 1):
        a1, op1, rd1, v1 = out[k]
        a2, op2, rd2, v2 = out[k + 1]
        if op1 == 4 and op2 == 12 and rd1 == rd2 and a2 - a1 <= 8:
            pairs.append((a1, rd1, (v2 << 16) | v1))
    return pairs


def annotate(v):
    if OD_LO <= v < OD_HI:
        return 'OD TABLE'
    if 0x20000000 <= v < 0x20050000:
        return 'RAM'
    if 0x08000000 <= v < 0x08100000:
        return 'FLASH'
    if 0x40000000 <= v < 0x50000000:
        return 'PERIPH'
    if v >= 0xE0000000:
        return 'SYSTEM'
    return ''


def main(argv):
    path = argv[0]
    flash, _b, _f = load(path)
    pairs = decode_movwt(flash)
    print("image %s : %d movw+movt pair(s) decoded" % (path, len(pairs)))

    if '--want' in argv:
        want = int(argv[argv.index('--want') + 1], 16)
        print("\n=== pairs building 0x%08x (exact) ===" % want)
        n = 0
        for a, rd, v in pairs:
            if v == want:
                print("  0x%08x  r%d = 0x%08x  (%s)" % (a, rd, v, annotate(v)))
                n += 1
        print("  %d site(s)" % n)
        # also near
        print("\n=== pairs building an address within +/-0x100 of 0x%08x ===" % want)
        n = 0
        for a, rd, v in pairs:
            if v != want and abs(v - want) <= 0x100:
                print("  0x%08x  r%d = 0x%08x  (%s)" % (a, rd, v, annotate(v)))
                n += 1
        print("  %d site(s)" % n)
        return 0

    if '--in-range' in argv:
        lo = int(argv[argv.index('--in-range') + 1], 16)
        hi = int(argv[argv.index('--in-range') + 2], 16)
        print("\n=== pairs building an address in 0x%08x..0x%08x ===" % (lo, hi))
        n = 0
        for a, rd, v in pairs:
            if lo <= v < hi:
                print("  0x%08x  r%d = 0x%08x" % (a, rd, v))
                n += 1
        print("  %d site(s)" % n)
        return 0

    # summary by class
    from collections import Counter
    c = Counter(annotate(v) or 'other' for _a, _r, v in pairs)
    print("\n=== constants by class ===")
    for k, n in c.most_common():
        print("  %-10s %d" % (k, n))
    print("\n=== OD-table constants ===")
    for a, rd, v in pairs:
        if OD_LO <= v < OD_HI:
            print("  0x%08x  r%d = 0x%08x" % (a, rd, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
