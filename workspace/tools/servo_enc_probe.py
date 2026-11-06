"""servo_enc_probe.py - is a servo firmware code region plain Thumb code or
enciphered data?

Plain ARM code has a spread-out word-value distribution; enciphered/compressed
data clusters or looks uniform.  Also checks for the tell-tale of a
self-synchronising stream cipher once it has gone wrong.

usage: python tools\\servo_enc_probe.py <file> <flash_addr_hex> <len_hex>
"""
import sys, os, struct, collections, math, hashlib

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table")


def entropy(b):
    if not b:
        return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def main(argv):
    path = argv[0]
    addr = int(argv[1], 16)
    ln = int(argv[2], 16)
    d, hdr, flash = load(path)
    off = addr - FLASH_BASE
    seg = flash[off:off + ln]
    print("%s  hdr=0x%x" % (os.path.basename(path), hdr))
    print("region 0x%08x..0x%08x (%d B)  md5 %s" %
          (addr, addr + len(seg), len(seg), hashlib.md5(seg).hexdigest()))
    print("  entropy %.3f bits/byte" % entropy(seg))
    print()

    print("=== 4-byte word value distribution (first 0x8000) ===")
    w = seg[:0x8000]
    vals = [struct.unpack_from('<I', w, i)[0] for i in range(0, len(w) - 4, 4)]
    print("  words: %d" % len(vals))
    bands = collections.Counter()
    for v in vals:
        bands[v >> 16] += 1
    print("  top 12 high-16-bit bands:")
    for b, n in bands.most_common(12):
        print("    0x%04x0000..0x%04xffff  x%d" % (b, b, n))
    # how many words look like valid Thumb code addresses?
    thumbish = sum(1 for v in vals if 0x08000000 <= (v & ~1) < 0x08100000)
    print("  words that look like Thumb code pointers (0x080xxxxx): %d (%.1f%%)" %
          (thumbish, 100.0 * thumbish / len(vals)))

    print()
    print("=== Thumb opcode sanity (how many halfwords are plausible?) ===")
    hw = [struct.unpack_from('<H', seg, i)[0] for i in range(0, min(len(seg), 0x8000) - 2, 2)]
    push_lr = sum(1 for x in hw if (x & 0xff00) == 0xb500)
    bl_hi = sum(1 for x in hw if (x & 0xf800) == 0xf000)
    print("  halfwords %d ; push{r..,lr}(0xb5xx) %d ; BL-hi(0xf0xx) %d ; ratio %.3f" %
          (len(hw), push_lr, bl_hi, (push_lr + bl_hi) / len(hw)))

    print()
    print("=== first 64 bytes of the region ===")
    for i in range(0, 64, 16):
        b = seg[i:i + 16]
        print("  0x%08x  %s" % (addr + i, b.hex(' ')))
    print()
    print("=== compare with the same flash address in the other file? (caller's job) ===")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
