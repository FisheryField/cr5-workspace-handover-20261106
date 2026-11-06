"""servo_hot.py - find the flash regions where two servo firmware builds are
*most* similar.

The two builds are ~2-5% identical overall, but a few windows reach ~21%.  Those
are the only places where cross-version diffing can work, so they are worth
locating precisely and reading.

usage: python tools\\servo_hot.py <new.bin> <old.bin> [--blk N] [--top N]
"""
import sys, os, struct, hashlib, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    blk = int(argv[argv.index('--blk') + 1], 0) if '--blk' in argv else 0x200
    top = int(argv[argv.index('--top') + 1]) if '--top' in argv else 40
    _dn, _bn, fn = load(new_p)
    _do, _bo, fo = load(old_p)
    n = min(len(fn), len(fo))
    print("new %s %d B / old %s %d B  (comparing %d B)" %
          (os.path.basename(new_p), len(fn), os.path.basename(old_p), len(fo), n))
    print("block size 0x%x" % blk)
    print()

    blocks = []
    for off in range(0, n - blk + 1, blk):
        A, B = fn[off:off + blk], fo[off:off + blk]
        same = sum(1 for i in range(blk) if A[i] == B[i])
        blocks.append((off, same / blk))

    hist = {}
    for off, r in blocks:
        hist[int(r * 10)] = hist.get(int(r * 10), 0) + 1
    print("=== identity histogram (deciles of %) ===")
    for k in sorted(hist):
        print("   %2d-%2d%%  %5d blocks  %s" % (k * 10, k * 10 + 10, hist[k], '#' * min(60, hist[k] // 4)))

    print()
    print("=== hottest blocks ===")
    hot = sorted(blocks, key=lambda t: -t[1])[:top]
    for off, r in hot:
        print("  0x%08x  %6.2f%%" % (FLASH_BASE + off, r * 100))

    # merge neighbouring hot blocks into regions
    HOT = 0.15
    regions = []
    for off, r in sorted(blocks):
        if r >= HOT:
            if regions and off == regions[-1][1]:
                regions[-1][1] = off + blk
                regions[-1][2] = max(regions[-1][2], r)
            else:
                regions.append([off, off + blk, r])
    print()
    print("=== contiguous regions with >= %.0f%% identity ===" % (HOT * 100))
    for a, b, r in regions:
        print("  0x%08x..0x%08x  (%5d B)  best %.1f%%" % (FLASH_BASE + a, FLASH_BASE + b, b - a, r * 100))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                       'servo_fw_samples', 'hot_regions.json')
    json.dump([{"start": FLASH_BASE + a, "end": FLASH_BASE + b, "best": r} for a, b, r in regions],
              open(out, 'w'), indent=1)
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
