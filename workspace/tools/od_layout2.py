"""od_layout2.py - determine the true structure of the servo OD metadata table.

Observed (tools/od_layout.py output) around Home offset:

    0x0802537e  "Home offset\\0"
                05 00 08 00 07 00      <- 6-byte record, 4th byte = 0x07
                04 00 20 00 3f 00      <- 4th byte = 0x04
                04 00 20 00 3f 00
                04 00 20 00 3f 00

i.e. a name is followed by a RUN of 6-byte records, and the last byte is 0x04 or
0x07 for most names.  Hypothesis to test: the table is a flat array of 6-byte
records, and each name is followed by a variable-length run of them.

This script:
  1. finds the alignment of the 6-byte record grid by scoring every phase
  2. walks the run after every name and prints the decoded run
  3. scores "run lengths" and the last-byte values to see what terminates a run

usage:
  python tools\\od_layout2.py <flash.bin>
  python tools\\od_layout2.py <flash.bin> --align
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


def score_records(buf, phase, lo, hi):
    """Count records at offsets lo+phase, lo+phase+6, ... that look valid."""
    good = bad = 0
    o = lo + phase
    while o + REC <= hi:
        t, th, b, bh, a, ah = buf[o:o + 6]
        if th == 0 and bh == 0 and ah == 0 and t in TYPE and b in (8, 16, 32):
            good += 1
        else:
            bad += 1
        o += REC
    return good, bad


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    lo = 0x08024985 - FLASH_BASE
    hi = 0x0802642e - FLASH_BASE

    if '--align' in argv or len(argv) == 1:
        print("=== 6-byte record grid: score each phase over 0x08024985..0x0802642e ===")
        for ph in range(REC):
            g, b = score_records(flash, ph, lo, hi)
            print("  phase %d: valid=%4d invalid=%4d  (%.1f%%)" %
                  (ph, g, b, 100.0 * g / max(1, g + b)))

    names = []
    for m in re.finditer(rb"[\x20-\x7e]{4,}\x00", flash[lo:hi]):
        names.append((lo + m.start(), lo + m.end(), m.group()[:-1].decode('ascii')))

    # Where does the flat 6-byte record grid actually start matching?
    # Try each name's record start and walk the run.
    print("\n=== runs of 6-byte records after each name (using phase of table start) ===")
    lastb = collections.Counter()
    runlens = collections.Counter()
    for i, (s, e, n) in enumerate(names):
        run = []
        o = e
        while o + REC <= hi:
            t, th, b, bh, a, ah = flash[o:o + REC]
            if th == 0 and bh == 0 and ah == 0 and t in TYPE and b in (8, 16, 32):
                run.append((t, b, a))
                o += REC
            else:
                break
        if run:
            lastb[run[-1][2]] += 1
            runlens[len(run)] += 1
        desc = ' '.join("%s/%d/a=%02x" % (TYPE[t], b, a) for t, b, a in run[:6])
        print("0x%08x %-36s run=%2d  %s" % (FLASH_BASE + s, n[:36], len(run), desc))

    print("\n=== last-record attr value histogram ===")
    for k, v in lastb.most_common():
        print("  a=0x%02x : %d" % (k, v))
    print("\n=== run length histogram ===")
    for k, v in sorted(runlens.items()):
        print("  run=%-3d : %d" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
