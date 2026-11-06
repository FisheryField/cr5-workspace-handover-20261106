"""hparam_table_find.py - look for the vendor parameter-map index tables inside the
servo firmware image.

Reasoning: data/official/servoCSV/param.csv gives each H-parameter a
`ParaMapIndex` (0..259).  That column is NOT derivable from (group, sub), so it is
a real index - most likely an index into a firmware table.  If the firmware holds
a per-parameter record array, the ParaMapIndex values should appear as a
permutation-like run of small integers (0..259) somewhere in the image.

This script:
  1. builds the ParaMapIndex permutation from param.csv
  2. finds the longest/ densest run of distinct values in 0..0x120 in the image
  3. for each candidate table, prints it aligned against the vendor map so a
     match (or a systematic relation) is visible

usage:
  python tools\\hparam_table_find.py <flash.bin> [--csv data/official/servoCSV/param.csv]
"""
import sys, os, struct, csv, io, json, re
from collections import Counter

FLASH_BASE = 0x08000000
DEFAULT_CSV = os.path.join('data', 'official', 'servoCSV', 'param.csv')
# the parameter-map index space, plus slack for a possible +1 offset or terminator
VMAX = 0x140


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def load_vendor(path):
    raw = open(path, 'rb').read()
    for enc in ('gbk', 'gb18030', 'utf-8-sig'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(io.StringIO(text)))
    hi = next(i for i, r in enumerate(rows) if r and r[0].strip() == 'IsCheck')
    hdr = [h.strip() for h in rows[hi]]
    out = []
    for r in rows[hi + 1:]:
        if not r or not r[0].strip():
            continue
        d = dict(zip(hdr, r))
        pi = d.get('ParaIndex', '').strip()
        m = re.match(r'^H([0-9A-Fa-f]{2})\.(\d+)$', pi)
        if not m:
            continue
        try:
            mi = int(d.get('ParaMapIndex', '').strip() or -1)
        except ValueError:
            mi = -1
        out.append((mi, int(m.group(1), 16), int(m.group(2)), pi, d.get('ParaName', '').strip()))
    return out


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    csvp = argv[argv.index('--csv') + 1] if '--csv' in argv else DEFAULT_CSV
    vend = load_vendor(csvp)
    perm = sorted(mi for mi, _g, _s, _p, _n in vend if mi >= 0)
    print("vendor param.csv: %d entries, ParaMapIndex %d..%d (%d distinct)" %
          (len(vend), min(perm), max(perm), len(set(perm))))

    # a firmware table of small ints: scan for windows where values are in 0..VMAX
    # and mostly distinct
    W = 280
    best = []
    for o in range(0, len(flash) - 4 * W, 4):
        vals = struct.unpack_from('<%dI' % W, flash, o)
        if max(vals) >= VMAX:
            continue
        distinct = len(set(vals))
        if distinct >= W * 0.85:
            best.append((distinct, FLASH_BASE + o))
    best.sort(reverse=True)
    print("\n=== candidate tables of >=%d mostly-distinct small integers (0..0x%x) ===" % (int(W * 0.85), VMAX))
    if not best:
        print("  none found")
    for dist, a in best[:15]:
        print("  0x%08x  %d distinct / %d" % (a, dist, W))

    if best:
        print("\n=== closest candidate vs vendor permutation ===")
        dist, a = best[0]
        o = a - FLASH_BASE
        vals = list(struct.unpack_from('<%dI' % W, flash, o))
        print("  table @0x%08x first 40: %s" % (a, vals[:40]))
        print("  vendor  first 40:       %s" % perm[:40])
        vs = set(vals)
        ps = set(perm)
        print("  intersection with vendor index set: %d of %d" % (len(vs & ps), len(vs)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
