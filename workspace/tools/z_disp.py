#!/usr/bin/env python3
"""z_disp.py -- find every instruction whose memory displacement equals a value.

Hand-encodes the 16-bit Thumb load/store forms that carry a 5-bit immediate
(imm5 == 0x26 or 0xBD is out of range for those, so for 0xBD only `ldr/str`
imm12 and `add.w/addw/sub` forms matter).

why not just grep bytes: the byte pattern `26 8a` also occurs inside random
code, so each hit is printed with its decoded instruction for eyeballing, and a
positive control (a displacement known to exist) is required.

usage: python tools\\z_disp.py <tag> <imm> [<imm> ...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw


def scan_thumb16(f, imm):
    """imm5 forms: ldr/str/ldrb/strb/ldrh/strh with imm5 = imm (imm < 0x20)."""
    out = []
    if imm >= 0x20:
        return out
    c = f.code
    # opcode -> (mask, value)
    forms = [
        (0x6800, 0xF800, 'ldr'),    # 0110 1 imm5 Rn Rt
        (0x6000, 0xF800, 'str'),    # 0110 0
        (0x7800, 0xF800, 'ldrb'),   # 0111 1
        (0x7000, 0xF800, 'strb'),   # 0111 0
        (0x8800, 0xF800, 'ldrh'),   # 1000 1
        (0x8000, 0xF800, 'strh'),   # 1000 0
    ]
    for o in range(0, len(c) - 2, 2):
        w = struct.unpack_from('<H', c, o)[0]
        for val, mask, mn in forms:
            if (w & mask) != val:
                continue
            if ((w >> 6) & 0x1F) != imm:      # imm5 lives in bits 10..6
                continue
            out.append((f.base + o, mn, (w >> 3) & 7, w & 7))
    return out


def scan_add(f, imm):
    """add.w rD, rN, #imm12  (11110 i 0 1000 0 0 imm3 rN 0 imm8) and addw."""
    out = []
    c = f.code
    for o in range(0, len(c) - 4, 2):
        w1, w2 = struct.unpack_from('<HH', c, o)
        if (w1 & 0xFB80) == 0xF200 and (w2 & 0x8000) == 0:
            i = (w1 >> 10) & 1
            imm3 = (w2 >> 12) & 7
            imm8 = w2 & 0xFF
            v = (i << 11) | (imm3 << 8) | imm8
            if v == imm:
                out.append((f.base + o, 'add.w', (w2 >> 8) & 0xF, (w2 >> 0) & 0xF))
    return out


def main(argv):
    tag = argv[0]
    f = Fw(tag)
    for s in argv[1:]:
        imm = int(s, 0)
        print('== %s   displacement 0x%x' % (tag, imm))
        h16 = scan_thumb16(f, imm)
        print('   16-bit imm5 forms: %d' % len(h16))
        for a, mn, rt, rn in h16[:40]:
            print('      0x%08x  %-5s r%d,[r%d,#0x%x]' % (a, mn, rt, rn, imm))
        ha = scan_add(f, imm)
        print('   add.w immediate  : %d' % len(ha))
        for a, mn, rd, rn in ha[:40]:
            print('      0x%08x  %-6s r%d, r%d, #0x%x' % (a, mn, rd, rn, imm))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
