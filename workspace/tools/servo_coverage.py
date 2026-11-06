"""servo_coverage.py - measure how much of a servo firmware image has actually been
IDENTIFIED, as opposed to merely byte-counted.

Distinction that matters for a "what percentage is decoded?" question:

  * bytes counted        - trivial, tells you nothing
  * bytes classified     - is this Thumb code or data? (measurable)
  * bytes attributable   - do we know what it IS? (functions with a understood role)

This script produces the three separately, so a coverage claim can be made honestly.

Method for code-vs-data: linear sweep from the reset vector, decoding Thumb and
recording how far a coherent instruction stream runs.  That is optimistic (it will
happily decode padding), so it is cross-checked against a vector-table-based estimate:
every entry in the vector table is a real handler, giving a lower bound on function
count.

usage:
  python tools\\servo_coverage.py <flash.bin>
  python tools\\servo_coverage.py <flash.bin> --known 0x080016de:0x40 ...
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
    flash, hdr, _f = load(path)
    n = len(flash)
    print("image %s" % path)
    print("  payload %d B (0x%08x..0x%08x)" % (n, FLASH_BASE, FLASH_BASE + n))

    # ---- vector table -------------------------------------------------------
    vec = []
    for o in range(0, min(0x200, n), 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if 0x08000000 <= v < 0x08000000 + n:
            vec.append((FLASH_BASE + o, v))
    print("\n=== vector table ===")
    print("  %d entries pointing into the image" % len(vec))
    if vec:
        print("  first handlers: %s" % ' '.join('0x%x' % v for _a, v in vec[:10]))

    # ---- linear Thumb sweep -------------------------------------------------
    decodable = 0
    total = 0
    for a in range(FLASH_BASE, FLASH_BASE + n - 4, 2):
        total += 1
        if list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a)):
            decodable += 1
    print("\n=== linear Thumb sweep (optimistic: decodes padding too) ===")
    print("  decodable halfwords: %d / %d = %.1f%%" % (decodable, total, 100.0 * decodable / total))

    # ---- structural: 0x00 / 0xff padding ------------------------------------
    zeros = flash.count(0)
    ff = flash.count(0xff)
    print("\n=== byte composition ===")
    print("  0x00 bytes : %d (%.1f%%)" % (zeros, 100.0 * zeros / n))
    print("  0xff bytes : %d (%.1f%%)" % (ff, 100.0 * ff / n))
    print("  other      : %d (%.1f%%)" % (n - zeros - ff, 100.0 * (n - zeros - ff) / n))

    # ---- printable-string bytes (identifiable data) -------------------------
    import re
    sbytes = sum(len(m.group()) for m in re.finditer(rb'[\x20-\x7e]{4,}', flash))
    print("  printable runs >=4 chars: %d B (%.1f%%)" % (sbytes, 100.0 * sbytes / n))

    # ---- the pieces this session actually identified ------------------------
    KNOWN = {
        'OD metadata table': (0x08024991, 0x0802642e),
        'OD names (whole run)': (0x08024bd0, 0x0802642e),
        'flash HAL (unlock/program/lock)': (0x0800433c, 0x08004530),
        'param persist routine': (0x080016de, 0x08001708),
        'param persist (full)': (0x080016de, 0x08001860),
        'log append': (0x080017d0, 0x08001860),
        'NV param API': (0x080045a8, 0x08004620),
        'sector classifier': (0x08009bf8, 0x08009c9c),
        'inline descriptor region': (0x08051300, 0x08052800),
    }
    if '--known' in argv:
        for spec in argv[argv.index('--known') + 1:]:
            lo, ln = spec.split(':')
            KNOWN['extra ' + lo] = (int(lo, 16), int(lo, 16) + int(ln, 16))
    print("\n=== regions this session actually identified ===")
    tot = 0
    for name, (lo, hi) in sorted(KNOWN.items(), key=lambda kv: kv[1][0]):
        sz = hi - lo
        tot += sz
        print("  %-32s 0x%08x..0x%08x  %6d B  %.2f%%" %
              (name, lo, hi, sz, 100.0 * sz / n))
    print("  ---------------------------------------------------------")
    print("  total identified (with overlaps): %d B = %.2f%% of image" % (tot, 100.0 * tot / n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
