"""hexmap.py - parse an Intel HEX file and report its address coverage.

Answers a question the package manifest only asserts: which flash addresses does
the 3.1.5 dump actually contain, and where are the dense code regions?

usage: python tools\\hexmap.py <file.hex> [--gaps N]
"""
import sys, collections


def parse(path):
    segs = []          # (addr, bytes)
    ext = 0
    bad = 0
    lines = 0
    with open(path, 'r', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line.startswith(':'):
                continue
            lines += 1
            try:
                n = int(line[1:3], 16)
                a = int(line[3:7], 16)
                t = int(line[7:9], 16)
                data = bytes.fromhex(line[9:9 + n * 2])
                ck = int(line[9 + n * 2:11 + n * 2], 16)
            except Exception:
                bad += 1
                continue
            s = (sum(line[1:9 + n * 2].encode()) if False else
                 (n + (a >> 8) + (a & 0xff) + t + sum(data)) & 0xff)
            calc = (-s) & 0xff
            if calc != ck:
                bad += 1
            if t == 0:
                segs.append((ext + a, data))
            elif t == 4:
                ext = int.from_bytes(data, 'big') << 16
            elif t == 2:
                ext = int.from_bytes(data, 'big') << 4
    return segs, lines, bad


def main(argv):
    path = argv[0]
    segs, lines, bad = parse(path)
    print("%s: %d records, %d checksum errors" % (path, lines, bad))
    if not segs:
        return 1
    data = {}
    for a, d in segs:
        for i, b in enumerate(d):
            data[a + i] = b
    lo, hi = min(data), max(data)
    print("address span 0x%08x .. 0x%08x (%d bytes of data)" % (lo, hi, len(data)))

    # density map per 4 KiB
    print()
    print("=== per-4KiB coverage (dense = code) ===")
    buckets = collections.Counter()
    for a in data:
        buckets[a >> 12] += 1
    for k in sorted(buckets):
        n = buckets[k]
        bar = '#' * min(50, n * 50 // 4096)
        print("  0x%08x  %4d B  %s" % (k << 12, n, bar))

    # contiguous runs of the full image
    print()
    print("=== contiguous data runs >= 1 KiB ===")
    runs = []
    start = prev = None
    for a in sorted(data):
        if start is None:
            start = prev = a
        elif a == prev + 1:
            prev = a
        else:
            runs.append((start, prev + 1))
            start = prev = a
    if start is not None:
        runs.append((start, prev + 1))
    for a, b in runs:
        if b - a >= 1024:
            print("  0x%08x .. 0x%08x  (%d B)" % (a, b, b - a))
    print("  total runs: %d ; runs >= 1 KiB: %d" % (len(runs), sum(1 for a, b in runs if b - a >= 1024)))

    # does the first 32 bytes of the other firmware show up?
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
