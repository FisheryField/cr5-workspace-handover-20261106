"""servo_hparam_refs.py - does either servo image reference the vendor H-parameter
EtherCAT addresses (0x20GG:sub) anywhere?

Rationale: SERVO_PERSIST_FINDING.md established the vendor parameter map from the
official CSV - H01.17 "encoder position angle" -> 0x2001:18, H0C.02 "encoder zero
calibration enable" -> 0x200C:3, and so on.  The zero-point question is whether the
DRIVE firmware itself knows about those parameters.  A cheap, decisive check: look for
the index values in instruction immediates and in literal-pool data.

Index space of interest: 0x2000..0x200F (the vendor groups H00..H0F).

usage:
  python tools\\servo_hparam_refs.py <flash.bin>
  python tools\\servo_hparam_refs.py <flash.bin> --idx 0x2001 --sub 0x12
"""
import sys, struct
from collections import Counter

FLASH_BASE = 0x08000000
LO, HI = 0x2000, 0x2010


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def thumb_imms(flash):
    """Decode movw / movs immediates (the two Thumb forms that carry a small constant)."""
    out = []
    n = len(flash)
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 4:
        hw = struct.unpack_from('<H', flash, a - FLASH_BASE)[0]
        hw2 = struct.unpack_from('<H', flash, a - FLASH_BASE + 2)[0]
        if (hw & 0xF800) == 0x2000:
            out.append((a, hw & 0xFF, 'movs'))
        elif (hw & 0xFB00) == 0xF200 and ((hw >> 4) & 0xF) == 4:
            i = (hw >> 10) & 1
            v = (i << 11) | ((hw & 0xF) << 12) | (((hw2 >> 12) & 7) << 8) | (hw2 & 0xFF)
            out.append((a, v, 'movw'))
        a += 2
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    flash = load(path)[2]
    print("image %s (%d B)" % (path, len(flash)))

    # 1. index as instruction immediate
    print("\n=== vendor index 0x20GG as an instruction immediate ===")
    hits = [(a, v, k) for a, v, k in thumb_imms(flash) if LO <= v < HI]
    if hits:
        for a, v, k in hits:
            print("    0x%08x  %-5s 0x%04X" % (a, k, v))
    else:
        print("    (none)")

    # 2. index as a literal-pool dword / halfword
    print("\n=== vendor index 0x20GG as literal-pool DATA (4-byte grid dword) ===")
    n = 0
    for o in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if LO <= v < HI:
            print("    0x%08x = 0x%08X" % (FLASH_BASE + o, v))
            n += 1
    print("    %d site(s)" % n)

    print("\n=== 16-bit scan: halfword 0x20GG (may be a false positive on code bytes) ===")
    c = Counter()
    for o in range(0, len(flash) - 2, 2):
        v = struct.unpack_from('<H', flash, o)[0]
        if LO <= v < HI:
            c[v] += 1
    if c:
        for v, k in sorted(c.items()):
            print("    0x%04X : %d" % (v, k))
    else:
        print("    (none)")

    # 3. what the wide immediate survey says about the whole 0x2000..0x2100 band
    print("\n=== instruction immediates across 0x1FF0..0x2100 (context) ===")
    band = sorted({v for _a, v, _k in thumb_imms(flash) if 0x1FF0 <= v < 0x2100})
    print("    %s" % ' '.join('0x%X' % v for v in band) if band else "    (none)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
