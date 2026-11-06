"""servo_fpconst.py - resolve the double-precision constants loaded by `vldr dN,[pc,#n]`.

Why hand calculation failed: the PC base for a 32-bit Thumb `vldr` is `align4(addr+4)`, and
getting the offset wrong by one instruction yields a completely unrelated 8-byte value
(an earlier hand computation produced -3.09e+207, obviously wrong).  This script lets
capstone decode the instruction and reports the resolved 8-byte value both as raw bits
and as a double, so the number can be sanity-checked.

usage:
  python tools\\servo_fpconst.py <flash.bin> --at 0x08014a46
  python tools\\servo_fpconst.py <flash.bin> --at 0x08014a46 --window 0x20
"""
import sys, struct

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    flash = load(path)[2]
    at = int(argv[argv.index('--at') + 1], 16)
    win = int(argv[argv.index('--window') + 1], 16) if '--window' in argv else 0x20

    print("scanning 0x%08x .. 0x%08x for vldr/vstr with pc-relative literal" % (at, at + win))
    found = 0
    for i in md.disasm(flash[at - FLASH_BASE:at - FLASH_BASE + win], at):
        if 'pc' in i.op_str and ('vldr' in i.mnemonic or 'vstr' in i.mnemonic):
            try:
                off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
            except (ValueError, IndexError):
                continue
            tgt = ((i.address + 4) & ~3) + off
            if not (FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 8):
                print("  0x%08x %-20s -> 0x%08x (out of range)" % (i.address, i.op_str, tgt))
                continue
            raw = struct.unpack_from('<Q', flash, tgt - FLASH_BASE)[0]
            dv = struct.unpack('<d', struct.pack('<Q', raw))[0]
            fv = struct.unpack_from('<f', flash, tgt - FLASH_BASE)[0]
            import math
            printable = ('%.12g' % dv) if math.isfinite(dv) else '(non-finite)'
            print("  0x%08x %-22s -> lit 0x%08x" % (i.address, i.op_str, tgt))
            print("      raw64 = 0x%016X" % raw)
            print("      double = %s" % printable)
            print("      (first 4 bytes as float = %.9g)" % fv)
            found += 1
    if not found:
        print("  (no pc-relative vldr/vstr found in window)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
