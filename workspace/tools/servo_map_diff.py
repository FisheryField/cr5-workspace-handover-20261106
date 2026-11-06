"""servo_map_diff.py - byte-identity map between two firmware builds.

Because the two releases have code inserted/reordered early on, a single global
shift cannot align them.  This prints, per 4 KiB block of flash, the byte
identity ratio at the same address, which shows exactly where the two builds
diverge and where they are still identical.

usage: python tools\\servo_map_diff.py <new.bin> <old.bin> [--blk N]
"""
import sys, os, struct

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    new_p, old_p = argv[0], argv[1]
    blk = int(argv[argv.index('--blk') + 1]) if '--blk' in argv else 0x1000
    dn, bn, fn = load(new_p)
    do, bo, fo = load(old_p)
    # new flash 0x08000000.. ; old flash 0x08010000.. (per its manifest)
    print("new flash base 0x%08x (%d B)" % (FLASH_BASE, len(fn)))
    print("old flash base 0x08010000 (%d B)  [per package manifest]" % len(fo))
    print()
    print("%-14s %-14s %8s  %s" % ("new_addr", "old_addr", "ident", "bar"))
    n_blocks = (min(len(fn) - (0x08010000 - FLASH_BASE), len(fo)) + blk - 1) // blk
    tot_same = tot_cmp = 0
    identical_blocks = 0
    for k in range(n_blocks):
        na = (0x08010000 - FLASH_BASE) + k * blk
        oa = k * blk
        A = fn[na:na + blk]
        B = fo[oa:oa + blk]
        n = min(len(A), len(B))
        if n == 0:
            break
        same = sum(1 for i in range(n) if A[i] == B[i])
        tot_same += same
        tot_cmp += n
        r = same / n
        if r == 1.0:
            identical_blocks += 1
        bar = "#" * int(r * 40)
        if r < 1.0 or k < 4 or k % 16 == 0:
            print("0x%08x   0x%08x   %6.1f%%  %s" %
                  (0x08010000 + k * blk, 0x08010000 + k * blk, r * 100, bar))
    print()
    print("overall byte identity at the same address: %d/%d = %.2f%%" %
          (tot_same, tot_cmp, 100.0 * tot_same / tot_cmp))
    print("4 KiB blocks that are byte-identical: %d / %d" % (identical_blocks, n_blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
