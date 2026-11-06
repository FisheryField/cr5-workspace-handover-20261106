"""od_addr_hunt.py - hunt for the vendor H-parameter addresses in the servo image.

Goal (blocker A of SERVO_FW_OD_FINDING.md): the OD metadata table contains no
parameter address, so the mapping "OD entry -> vendor parameter address" must
live in code or in a second array.  Rather than keep guessing the table shape,
this script looks for the addresses themselves.

Known ground truth from the field (EtherCAT SDO traffic, SERVO_PARAM_CHANNEL.md):

    addr200C01 -> index 0x200C subIndex 1     (H0C.00)
    addr200118 -> index 0x2001 subIndex 18    (H01.17)

So real vendor parameter addresses are index 0x2000 | group, where observed
groups are 0x01 and 0x0C.  If the firmware holds a table of such parameters, the
literal 32-bit value 0x0000200C or 0x00002001 (or the pair form 0x200C0001)
should appear as data.

This script:
  1. counts literal occurrences of candidate encodings
  2. for each site, decodes the surrounding dwords as a candidate record array
  3. reports the best-scoring record stride

usage:
  python tools\\od_addr_hunt.py <flash.bin>
  python tools\\od_addr_hunt.py <flash.bin> --want 0x200C
"""
import sys, struct, collections

FLASH_BASE = 0x08000000
TYPE = {0x02: 'i8', 0x03: 'i16', 0x04: 'i32', 0x05: 'u8', 0x06: 'u16', 0x07: 'u32'}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    print("image 0x%08x..0x%08x (%d B)" % (FLASH_BASE, FLASH_BASE + len(flash), len(flash)))

    wants = [int(x, 16) for x in (argv[argv.index('--want') + 1].split(',')
                                  if '--want' in argv else ['0x200C', '0x2001', '0x2000'])]

    print("\n=== literal dword occurrences (4-byte aligned) ===")
    for w in wants:
        hits = []
        for o in range(0, len(flash) - 4, 4):
            v = struct.unpack_from('<I', flash, o)[0]
            if v == w or v == w << 16:
                hits.append((FLASH_BASE + o, v))
        print("  value 0x%08x / 0x%08x : %d sites" % (w, w << 16, len(hits)))
        for a, v in hits[:12]:
            print("     0x%08x = 0x%08x" % (a, v))
        if len(hits) > 12:
            print("     ... (%d more)" % (len(hits) - 12))

    print("\n=== all dwords in the vendor group range 0x2000..0x20FF (4-byte aligned) ===")
    grp = collections.Counter()
    sites = []
    for o in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if 0x2000 <= v <= 0x20FF:
            grp[v] += 1
            sites.append((FLASH_BASE + o, v))
    print("  total %d sites, %d distinct values" % (len(sites), len(grp)))
    for v, n in grp.most_common(40):
        print("    0x%04x : %d" % (v, n))

    print("\n=== clustered sites (>=3 vendor-group values within 64 B) ===")
    sites_sorted = sorted(sites)
    clusters = []
    cur = [sites_sorted[0]] if sites_sorted else []
    for a, v in sites_sorted[1:]:
        if a - cur[-1][0] <= 64:
            cur.append((a, v))
        else:
            if len(cur) >= 3:
                clusters.append(cur)
            cur = [(a, v)]
    if len(cur) >= 3:
        clusters.append(cur)
    print("  %d clusters" % len(clusters))
    for c in clusters[:10]:
        print("   0x%08x..0x%08x  %d values: %s" %
              (c[0][0], c[-1][0], len(c),
               ' '.join('%04x' % v for _a, v in c[:16])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
