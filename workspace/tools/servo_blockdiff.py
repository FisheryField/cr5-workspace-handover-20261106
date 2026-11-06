"""servo_blockdiff.py - locate the EXACT regions where the two servo images differ.

Method: greedy anchor-and-extend.
  1. anchor on a 32-byte marker unique in B, extend the match backwards and forwards
     byte-by-byte to the true equal-block boundaries
  2. step past the block and repeat
  3. the gaps between equal blocks are the CHANGED regions of A and B, with sizes

This is the honest counterpart to tools/servo_bindiff.py, which only reported a shift
profile (253 jump regions) and could not name block boundaries.  Knowing the exact
changed regions lets the changed code be triaged instead of guessed.

usage:
  python tools\\servo_blockdiff.py <a.bin> <b.bin> [--min 8] [--top 40]
"""
import sys, struct, hashlib

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    A = load(argv[0])[2]
    B = load(argv[1])[2]
    MIN = int(argv[argv.index('--min') + 1]) if '--min' in argv else 8
    TOP = int(argv[argv.index('--top') + 1]) if '--top' in argv else 40
    K = 32
    print("A %s (%d B)" % (argv[0], len(A)))
    print("B %s (%d B)" % (argv[1], len(B)))

    # index B by 32-byte marker -> position (keep one)
    idx = {}
    for o in range(0, len(B) - K):
        idx.setdefault(hashlib.blake2b(B[o:o + K], digest_size=8).digest(), o)

    i = j = 0
    blocks = []        # equal blocks: (a_start, b_start, length)
    while i <= len(A) - K and j <= len(B) - K:
        h = hashlib.blake2b(A[i:i + K], digest_size=8).digest()
        o = idx.get(h)
        if o is None:
            i += 1
            continue
        # extend backwards
        a2, b2 = i, o
        while a2 > 0 and b2 > 0 and A[a2 - 1] == B[b2 - 1]:
            a2 -= 1
            b2 -= 1
        # extend forwards
        e = min(len(A) - a2, len(B) - b2)
        n = 0
        while n < e and A[a2 + n] == B[b2 + n]:
            n += 1
        if n >= MIN:
            blocks.append((a2, b2, n))
            i = a2 + n
            j = b2 + n
        else:
            i += 1

    # merge/overshoot cleanup: keep blocks in order, drop overlaps
    clean = []
    last = -1
    for a2, b2, n in blocks:
        if a2 < last:
            continue
        clean.append((a2, b2, n))
        last = a2 + n
    blocks = clean

    eq = sum(n for _a, _b, n in blocks)
    print("\n=== equal blocks ===")
    print("  %d block(s), %d equal bytes = %.1f%% of A" % (len(blocks), eq, 100.0 * eq / len(A)))

    print("\n=== CHANGED regions of A (gaps between equal blocks) ===")
    regs = []
    prev = 0
    for a2, b2, n in blocks:
        if a2 > prev:
            regs.append((prev, a2 - prev))
        prev = a2 + n
    if prev < len(A):
        regs.append((prev, len(A) - prev))
    regs.sort(key=lambda t: -t[1])
    print("  %d region(s) totalling %d B" % (len(regs), sum(l for _o, l in regs)))
    for o, l in regs[:TOP]:
        print("    0x%08x .. 0x%08x   %6d B" % (FLASH_BASE + o, FLASH_BASE + o + l, l))
    if len(regs) > TOP:
        print("    ... (%d more, larger set suppressed)" % (len(regs) - TOP))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
