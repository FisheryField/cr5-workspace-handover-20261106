#!/usr/bin/env python3
"""z_disp32.py -- complete displacement scan, including the 32-bit Thumb-2
load/store forms (imm12) that the 16-bit-only scanner missed.

THIS GAP MATTERED: `ldr.w rX,[rY,#0x234]` (imm12) is how the firmware reaches
the position fields, while `ldr rX,[rY,#0x10]` (imm5) is how it reaches others.
A scanner that only knows the 16-bit forms reports "0 sites" for any offset
>= 0x20 -- i.e. exactly for every parameter slot number we care about.

32-bit encodings covered (first halfword / second halfword = Rt<<12 | imm12):
  LDR   T3 1111 1000 1101 Rn   0xF8D0+Rn
  LDRB  T2 1111 1000 1001 Rn   0xF890+Rn
  LDRH  T2 1111 1000 1011 Rn   0xF8B0+Rn
  LDRSB T2 1111 1001 1001 Rn   0xF990+Rn
  LDRSH T2 1111 1001 1011 Rn   0xF9B0+Rn
  STR   T3 1111 1000 1100 Rn   0xF8C0+Rn
  STRB  T2 1111 1000 1000 Rn   0xF880+Rn
  STRH  T2 1111 1000 1010 Rn   0xF8A0+Rn
plus the 16-bit imm5 forms and `adds Rd,#imm8` (0x3000) / `add.w`.

usage: python tools\\z_disp32.py <tag> <imm> [more...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw

WIDE = [
    (0xF8D0, 'ldr.w'), (0xF890, 'ldrb.w'), (0xF8B0, 'ldrh.w'),
    (0xF990, 'ldrsb.w'), (0xF9B0, 'ldrsh.w'),
    (0xF8C0, 'str.w'), (0xF880, 'strb.w'), (0xF8A0, 'strh.w'),
]
NARROW = [
    (0x6800, 0xF800, 'ldr'), (0x6000, 0xF800, 'str'),
    (0x7800, 0xF800, 'ldrb'), (0x7000, 0xF800, 'strb'),
    (0x8800, 0xF800, 'ldrh'), (0x8000, 0xF800, 'strh'),
]


def scan(f, imm):
    out = []
    c = f.code
    # wide (32-bit, imm12)
    for o in range(0, len(c) - 4, 2):
        w1, w2 = struct.unpack_from('<HH', c, o)
        base = w1 & 0xFFF0
        for val, mn in WIDE:
            if w1 & 0xFFF0 == val:
                if (w2 & 0xFFF) == imm:
                    out.append((f.base + o, mn, (w2 >> 12) & 0xF, w1 & 0xF, 32))
    # narrow (16-bit, imm5)
    if imm < 0x20:
        for o in range(0, len(c) - 2, 2):
            w = struct.unpack_from('<H', c, o)[0]
            for val, mask, mn in NARROW:
                if (w & mask) == val and ((w >> 6) & 0x1F) == imm:
                    out.append((f.base + o, mn, (w >> 3) & 7, w & 7, 16))
    # adds Rd,#imm8  (00110 Rd imm8) and add.w/addw
    if imm < 0x100:
        for o in range(0, len(c) - 2, 2):
            w = struct.unpack_from('<H', c, o)[0]
            if (w >> 11) == 0x6 and (w & 0xFF) == imm:
                out.append((f.base + o, 'adds', (w >> 8) & 7, (w >> 8) & 7, 16))
    return out


def main(argv):
    tag = argv[0]
    f = Fw(tag)
    for s in argv[1:]:
        imm = int(s, 0)
        hits = scan(f, imm)
        wide = [h for h in hits if h[4] == 32]
        print('== %s  displacement 0x%x : %d hit(s)  (%d wide / %d narrow)'
              % (tag, imm, len(hits), len(wide), len(hits) - len(wide)))
        for a, mn, rt, rn, w in hits[:60]:
            print('      0x%08x  %-8s r%d,[r%d,#0x%x]' % (a, mn, rt, rn, imm))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
