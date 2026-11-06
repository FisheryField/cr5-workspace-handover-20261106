"""servo_dec_check.py - validate the Thumb-2 add-immediate decoder against known bytes.

Motivation: tools/servo_poschain_cmp.py reported 142/143 `movw rX,#0x329` sites but
could not extract a single member offset, which means the ADD-immediate decoder is
wrong.  The known-good instruction is in the 0x6064 handler of 3.2.D.8:

    0x08002BC6  add.w r3, r3, #0x238      bytes:  03 f3 38 20

This script decodes the bytes, prints which bit fields carry what, and states the
correct mask/shift, so the caller can be fixed on evidence instead of memory.

usage:
  python tools\\servo_dec_check.py <flash.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000
SAMPLE = 0x08002bc6          # add.w r3, r3, #0x238   (expected imm 0x238)
SAMPLE2 = 0x08002bc8         # str   r3, [r0, #0x18]


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    flash, _b, _f = load(argv[0])

    for addr, expect in ((SAMPLE, 0x238), (SAMPLE2, None)):
        o = addr - FLASH_BASE
        b = flash[o:o + 4]
        hw1, hw2 = struct.unpack_from('<HH', flash, o)
        print("0x%08x  bytes=%s" % (addr, b.hex(' ')))
        print("   halfword1 = 0x%04x   binary = %s" % (hw1, format(hw1, '016b')))
        print("   halfword2 = 0x%04x   binary = %s" % (hw2, format(hw2, '016b')))
        print("   (hw1>>4)&0x1F = 0x%02x    hw1&0xFB00 = 0x%04x" % ((hw1 >> 4) & 0x1F, hw1 & 0xFB00))
        if expect is not None:
            i = (hw1 >> 10) & 1
            imm3 = (hw2 >> 12) & 0x7
            imm8 = hw2 & 0xFF
            dec = (i << 11) | (imm3 << 8) | imm8
            print("   decode attempt: i=%d imm3=%d imm8=0x%02x -> 0x%03x (expected 0x%03x) %s"
                  % (i, imm3, imm8, dec, expect, "OK" if dec == expect else "WRONG"))
            # also show the plain field split of halfword2
            print("   hw2 fields: [15:12]=0x%x [11:8]=0x%x [7:0]=0x%02x"
                  % ((hw2 >> 12) & 0xF, (hw2 >> 8) & 0xF, hw2 & 0xFF))
            print("   hw1 fields: Rn=[3:0]=0x%x  i=[10]=%d  op=[9:5]=0x%02x"
                  % (hw1 & 0xF, (hw1 >> 10) & 1, (hw1 >> 5) & 0x1F))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
