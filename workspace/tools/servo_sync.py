"""servo_sync.py - find the true alignment between two servo firmware payloads.

The two packages may start at different flash addresses, so brute-force the
byte offset of the old payload relative to the new one and score each candidate
by how many aligned 4-byte units match, then locally optimise.

usage: python tools\\servo_sync.py <new.bin> <old.bin>
"""
import sys, os, struct, hashlib

FLASH_BASE = 0x08000000
UNIT = 4


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def score(new, old, shift):
    """new[i] vs old[i+shift] on a 16-byte grid; returns (matches, compared)"""
    m = c = 0
    n = len(new)
    i = 0
    while i + 16 <= n:
        j = i + shift
        if 0 <= j and j + 16 <= len(old):
            c += 1
            if new[i:i + 16] == old[j:j + 16]:
                m += 1
        i += 16
    return m, c


def main(argv):
    new_p, old_p = argv[0], argv[1]
    dn, bn, fn = load(new_p)
    do, bo, fo = load(old_p)
    print("new %s  %d B  (payload 0x%08x..)" % (os.path.basename(new_p), len(fn), FLASH_BASE))
    print("old %s  %d B" % (os.path.basename(old_p), len(fo)))
    print()
    print("=== coarse scan: old_offset = new_offset + shift ===")
    best = []
    for shift in range(-0x20000, 0x20000 + 1, 0x100):
        m, c = score(fn, fo, shift)
        if c:
            best.append((m / c, shift, m, c))
    best.sort(reverse=True)
    for r, s, m, c in best[:8]:
        print("  shift %+7d (0x%+06x)  match %.4f  (%d/%d)" % (s, s, r, m, c))
    if not best:
        print("  no alignment found")
        return 1
    top = best[0][1]
    print()
    print("=== refine around %+d ===" % top)
    fine = []
    for shift in range(top - 0x100, top + 0x101, 4):
        m, c = score(fn, fo, shift)
        if c:
            fine.append((m / c, shift, m, c))
    fine.sort(reverse=True)
    for r, s, m, c in fine[:8]:
        print("  shift %+7d (0x%+06x)  match %.4f  (%d/%d)" % (s, s, r, m, c))
    r, s, m, c = fine[0]
    print()
    print("BEST: old is new shifted by %+d bytes (0x%+x)" % (s, s))
    if s > 0:
        print("  => old payload starts %d bytes EARLIER in flash than new" % s)
        print("  => old_flash_addr = new_flash_addr + 0x%x" % s)
    else:
        print("  => old payload starts %d bytes LATER in flash than new" % (-s))
        print("  => old_flash_addr = new_flash_addr - 0x%x" % (-s))
    # byte-level score for the winning shift
    m2 = sum(1 for i in range(len(fn)) if 0 <= i + s < len(fo) and fn[i] == fo[i + s])
    print("  byte-level identical: %d / %d (%.1f%%)" % (m2, len(fn), 100.0 * m2 / len(fn)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
