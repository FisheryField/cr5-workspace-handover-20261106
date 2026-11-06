"""servo_locate.py - decisive test: at which flash address does each package
start, and how similar are the two builds really?

Prints, for a set of candidate shifts, the byte-identity ratio of a 4 KiB
window taken from flash 0x08010000 in both images.

usage: python tools\\servo_locate.py <new.bin> <old.bin>
"""
import sys, os, struct, hashlib

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def ratio(a, b):
    n = min(len(a), len(b))
    if n == 0:
        return 0.0, 0
    same = sum(1 for i in range(n) if a[i] == b[i])
    return same / n, n


def main(argv):
    new_p, old_p = argv[0], argv[1]
    dn, bn, fn = load(new_p)
    do, bo, fo = load(old_p)
    print("new hdr=0x%x len=%d   old hdr=0x%x len=%d" % (bn, len(fn), bo, len(fo)))

    # sanity: are the two vendors' vector tables identical?
    print()
    print("=== vector table comparison (new[0:0x40] vs old[0:0x40]) ===")
    for i in range(0, 0x40, 16):
        a, b = fn[i:i + 16], fo[i:i + 16]
        print("  +0x%02x  new %s   old %s   %s" % (i, a.hex(' '), b.hex(' '), "SAME" if a == b else "DIFF"))
    same_vec = sum(1 for i in range(0x40) if fn[i] == fo[i])
    print("  identical bytes in the first 0x40: %d/64" % same_vec)

    # decisive: compare from flash 0x08010000 (the address the 3.1.5 manifest
    # declares as its start) in both images
    print()
    print("=== window comparison starting at flash 0x08010000 in BOTH images ===")
    WIN = 0x1000
    off_n = 0x08010000 - FLASH_BASE
    off_o = 0x08010000 - FLASH_BASE
    r, n = ratio(fn[off_n:off_n + WIN], fo[off_o:off_o + WIN])
    print("  new[0x%08x..] vs old[0x%08x..]  identical %.1f%% of %d B" %
          (0x08010000, 0x08010000, r * 100, n))
    print("  new window md5 %s" % hashlib.md5(fn[off_n:off_n + WIN]).hexdigest())
    print("  old window md5 %s" % hashlib.md5(fo[off_o:off_o + WIN]).hexdigest())

    print()
    print("=== search: best shift of the old image relative to the new one ===")
    best = (0.0, 0)
    win = fn[off_n:off_n + 0x2000]
    for sh in range(-0x8000, 0x8000 + 1, 2):
        base = off_n + sh
        if base < 0 or base + len(win) > len(fo):
            continue
        r, _ = ratio(win, fo[base:base + len(win)])
        if r > best[0]:
            best = (r, sh)
    print("  best: shift %+d bytes -> %.1f%% identical" % (best[1], best[0] * 100))
    print("  => old flash 0x%08x corresponds to new flash 0x%08x" %
          (0x08010000, 0x08010000 - best[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
