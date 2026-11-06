"""od_layout.py - re-examine the raw layout of the servo-firmware OD metadata table.

SERVO_FW_OD_FINDING.md claims a record is `name\\0` + 6 bytes (u16 type, u16 bits,
u16 attr).  A raw dump around "Home offset" shows the bytes after the name are
NOT 6 - the table appears to be a flat run of fixed-size sub-records interleaved
with name strings.

This script measures the real thing instead of assuming:

  * locate every NUL-terminated printable name in the table region
  * for each name, print the exact bytes that follow, up to the next name
  * classify the whole region as a byte-stream of 6-byte "descriptor" records
    and see where names sit relative to that grid

usage:
  python tools\\od_layout.py <flash.bin> [--lo 0x08024985] [--hi 0x0802642e]
  python tools\\od_layout.py <flash.bin> --name "Home offset"
"""
import sys, os, re, struct, json

FLASH_BASE = 0x08000000
TYPE = {0x02: 'i8', 0x03: 'i16', 0x04: 'i32', 0x05: 'u8', 0x06: 'u16', 0x07: 'u32'}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def find_names(flash, lo, hi):
    """All NUL-terminated printable runs >=4 chars inside [lo,hi] (file offsets)."""
    out = []
    for m in re.finditer(rb"[\x20-\x7e]{4,}\x00", flash[lo:hi]):
        out.append((lo + m.start(), lo + m.end(), m.group()[:-1].decode('ascii')))
    return out


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    lo = int(argv[argv.index('--lo') + 1], 16) - FLASH_BASE if '--lo' in argv else 0x08024985 - FLASH_BASE
    hi = int(argv[argv.index('--hi') + 1], 16) - FLASH_BASE if '--hi' in argv else 0x0802642e - FLASH_BASE

    if '--name' in argv:
        want = argv[argv.index('--name') + 1]
        names = find_names(flash, 0, len(flash))
        for s, e, n in names:
            if want.lower() in n.lower():
                nxt = min([s2 for s2, _e, _n in names if s2 > s] or [e + 32])
                blk = flash[e:min(nxt, e + 48)]
                print("0x%08x  %-32r +%d  next=0x%08x" % (FLASH_BASE + s, n, nxt - e, FLASH_BASE + nxt))
                print("   bytes: %s" % blk.hex(' '))
        return 0

    names = find_names(flash, lo, hi)
    print("region 0x%08x..0x%08x (%d B), %d printable NUL-terminated runs" %
          (FLASH_BASE + lo, FLASH_BASE + hi, hi - lo, len(names)))

    print("\n=== each name + the bytes until the next name ===")
    for i, (s, e, n) in enumerate(names):
        nxt = names[i + 1][0] if i + 1 < len(names) else hi
        trail = flash[e:nxt]
        print("0x%08x len=%-3d %-38s trail(%2d): %s" %
              (FLASH_BASE + s, len(n), n[:38], len(trail), trail.hex(' ')))

    print("\n=== how many names are followed by a valid 6-byte descriptor ===")
    ok = 0
    for s, e, n in names:
        if e + 6 > len(flash):
            continue
        t, b, a = flash[e], flash[e + 2], flash[e + 4]
        if flash[e + 1] == 0 and flash[e + 3] == 0 and flash[e + 5] == 0 \
           and t in TYPE and b in (8, 16, 32):
            ok += 1
    print("  %d / %d names have a valid type/bits descriptor immediately after" % (ok, len(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
