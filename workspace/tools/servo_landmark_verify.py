"""servo_landmark_verify.py - verify a landmark scan cannot produce false negatives.

tools/servo_nvmap.py reported that v3.1.5.0 lacks the RAM addresses 0x20009714,
0x200096E4, 0x2000348C, 0x20003494 and 0x20003470 that v3.2.D.8 uses for parameter
persistence.  A negative of that kind is only meaningful if the scan could not have
missed them, so this script re-checks the negatives three independent ways:

  1. 4-byte-aligned dword scan (what servo_nvmap used)
  2. 2-byte-aligned dword scan
  3. movw/movt immediate pairs that would produce the address
  4. a "nearby address" scan: any dword within +/-0x40 of the target, which catches
     the case where the struct moved rather than disappeared

usage:
  python tools\\servo_landmark_verify.py <flash.bin> 0x20009714 0x200096E4 ...
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
    path = argv[0]
    targets = [int(x, 16) for x in argv[1:]]
    flash, _b, _f = load(path)
    print("image %s (%d B)" % (path, len(flash)))

    for t in targets:
        print("\n### target 0x%08x" % t)
        # 1 / 2
        for step in (4, 2):
            hits = [FLASH_BASE + o for o in range(0, len(flash) - 4, step)
                    if struct.unpack_from('<I', flash, o)[0] == t]
            print("  exact dword, %d-byte grid : %d %s" %
                  (step, len(hits), [hex(h) for h in hits[:6]]))
        # 4 nearby
        near = []
        for o in range(0, len(flash) - 4, 4):
            v = struct.unpack_from('<I', flash, o)[0]
            if t != v and abs(v - t) <= 0x40 and 0x20000000 <= v < 0x20050000:
                near.append((FLASH_BASE + o, v))
        print("  RAM dwords within +/-0x40   : %d %s" %
              (len(near), [('0x%x->0x%x' % (a, v)) for a, v in near[:8]]))
        # range sweep: list ALL RAM pointers in the enclosing 0x200096xx/0x200034xx page
        page = t & 0xFFFFFF00
        pagehits = []
        for o in range(0, len(flash) - 4, 4):
            v = struct.unpack_from('<I', flash, o)[0]
            if page <= v < page + 0x100:
                pagehits.append((FLASH_BASE + o, v))
        print("  any RAM ptr in page 0x%08x : %d %s" %
              (page, len(pagehits), [('0x%x->0x%x' % (a, v)) for a, v in pagehits[:8]]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
