"""od_shape.py - settle the OD metadata table's true record shape.

Facts established so far (tools/od_layout.py, tools/od_layout2.py):
  * region 0x08024985..0x0802642e holds 212 printable NUL-terminated runs
  * a name is followed by a RUN of 6-byte records, not exactly one
  * a flat 6-byte grid over the region only validates 6-9% of slots, so the
    descriptors are interleaved with names of varying length
  * record format `[type:u8=0] [bits:u8=0] [attr:u8=0]` is confirmed by
    Control Word u16/16 a=0x87 (ro) and Target Position i32/32 a=0x07 (rw)

Hypothesis H at this point: the table is a packed array of
    { name, count, count x 6-byte descriptor }
and the byte right before the descriptor run is the count.

This script validates / falsifies that by measuring the byte immediately after
each NUL terminator against the measured run length of the following descriptors.

usage:
  python tools\\od_shape.py <flash.bin> [--region 0x08024985 0x0802642e]
"""
import sys, struct, re, collections

FLASH_BASE = 0x08000000
TYPE = {0x02: 'i8', 0x03: 'i16', 0x04: 'i32', 0x05: 'u8', 0x06: 'u16', 0x07: 'u32'}
REC = 6


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def valid_rec(b):
    t, th, bits, bh, a, ah = b
    return th == 0 and bh == 0 and ah == 0 and t in TYPE and bits in (8, 16, 32)


def walk(flash, start, limit):
    """Maximal run of valid 6-byte descriptors starting at `start`."""
    run, o = [], start
    while o + REC <= limit and valid_rec(flash[o:o + REC]):
        run.append(flash[o:o + REC])
        o += REC
    return run, o


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    lo = 0x08024985 - FLASH_BASE
    hi = 0x0802642e - FLASH_BASE

    names = [(lo + m.start(), lo + m.end(), m.group()[:-1].decode('ascii'))
             for m in re.finditer(rb"[\x20-\x7e]{4,}\x00", flash[lo:hi])]

    print("=== H: does the byte at name_end equal the following descriptor run length? ===")
    print("%-8s %-36s %-5s %-6s %-7s %s" % ("addr", "name", "byte0", "runlen", "match", "first desc"))
    agree = disagree = 0
    for s, e, n in names:
        if e + REC > hi:
            continue
        b0 = flash[e]
        # try run starting immediately at e (no count byte)
        run0, _ = walk(flash, e, hi)
        # try run starting at e+1 (count byte consumed)
        run1, _ = walk(flash, e + 1, hi)
        first = ''
        for t, bits, a in [(r[0], r[2], r[4]) for r in (run1 or run0)][:1]:
            first = "%s/%d/a=%02x" % (TYPE[t], bits, a)
        m = "YES" if b0 == len(run1) else ("no" if run1 else "-")
        if run1:
            agree += 1 if b0 == len(run1) else 0
            disagree += 0 if b0 == len(run1) else 1
        print("0x%08x %-36s 0x%02x   %-6d %-7s %s" %
              (FLASH_BASE + s, n[:36], b0, len(run1), m, first))

    print("\n  names with a count-byte-then-run shape: agreed=%d disagreed=%d" % (agree, disagree))

    print("\n=== alternative: run starts immediately at name end, byte0 is the LAST descriptor's attr ===")
    tot_ok = tot = 0
    for s, e, n in names:
        run, _ = walk(flash, e, hi)
        if len(run) == 1:
            tot += 1
            tot_ok += 1 if flash[e + 5] == run[-1][4] else 0
    print("  single-descriptor names: %d (trivially consistent)" % tot)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
