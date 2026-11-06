"""servo_bindiff.py - build a version-delta map between the two servo images.

Method: anchor-based binary diff, no symbols needed.

  1. pick a strong anchor (the reset handler address from the vector table, plus dense
     64-byte fingerprints sampled from image A)
  2. for each anchor, find where it landed in image B -> gives (offsetA, offsetB) pairs
     and therefore the local shift B-A
  3. sort the pairs by offsetA; between consecutive anchors the shift is constant, so
     report the SHIFT PROFILE: which address ranges of A are shifted by how much, and
     where the shift changes - a shift change marks inserted/deleted data
  4. summarise: where is B longer, i.e. where did the extra ~9 KB of A come from
     (A is 338,072 B, B is 328,860 B -> A has 9,212 B more)

This is the direct answer to "what did 3.2.D.8 change", at the binary level.

usage:
  python tools\\servo_bindiff.py <a.bin> <b.bin> [--step 64] [--min-run 3]
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


def fingerprints(data, step, k=32):
    """Sampled (hash -> offset) index for anchors."""
    idx = {}
    for o in range(0, len(data) - k, step):
        idx.setdefault(hashlib.blake2b(data[o:o + k], digest_size=8).digest(), []).append(o)
    return idx


def main(argv):
    A, _b, _f = load(argv[0])
    B, _b2, _f2 = load(argv[1])
    step = int(argv[argv.index('--step') + 1]) if '--step' in argv else 64
    K = 32
    print("A %s : %d B" % (argv[0], len(A)))
    print("B %s : %d B" % (argv[1], len(B)))
    print("size delta A-B = %d B" % (len(A) - len(B)))

    idxb = fingerprints(B, 1, K)          # exhaustive on B so any anchor can be found
    pairs = []
    o = 0
    while o < len(A) - K:
        h = hashlib.blake2b(A[o:o + K], digest_size=8).digest()
        for cand in idxb.get(h, ())[:1]:
            pairs.append((o, cand))
            break
        o += step
    print("\nanchors matched: %d (sampled every %d B of A)" % (len(pairs), step))
    if not pairs:
        return 1

    pairs.sort()
    # shift profile
    print("\n=== shift profile (A offset -> B offset, shift) ===")
    print("  %-12s %-12s %-10s" % ("A", "B", "shift"))
    runs = []
    cur = None
    for a, b in pairs:
        sh = b - a
        if cur is None or sh != cur[2]:
            if cur:
                runs.append(cur)
            cur = [a, b, sh, 1]
        else:
            cur[3] += 1
            cur[1] = b
    if cur:
        runs.append(cur)
    for a, b, sh, cnt in runs:
        print("  0x%08x   0x%08x   %+d   (span %d anchors)" %
              (FLASH_BASE + a, FLASH_BASE + b, sh, cnt))

    print("\n=== interpretation ===")
    if len(runs) == 1:
        print("  single constant shift %+d -> the two images differ only by an" % runs[0][2])
        print("  insertion/deletion at ONE place.  Locate it at the boundary.")
    else:
        print("  %d shift regions -> %d insertion/deletion boundaries."
              % (len(runs), len(runs) - 1))
        for i in range(len(runs) - 1):
            a1 = runs[i][0]
            a2 = runs[i + 1][0]
            dsh = runs[i + 1][2] - runs[i][2]
            print("    boundary near A=0x%08x .. 0x%08x : shift jumps by %+d B"
                  % (FLASH_BASE + a1, FLASH_BASE + a2, dsh))
            print("       -> in B the extra data sits around 0x%08x"
                  % (FLASH_BASE + runs[i][1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
