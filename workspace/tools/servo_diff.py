"""servo_diff.py - function-level diff between two servo firmware versions.

Both files are FoE payloads: a 0x20-byte vendor header then the raw Cortex-M
flash image based at 0x08000000.  This aligns them by address, finds the
differing regions, and prints disassembly around each change.

usage: python tools\\servo_diff.py <new.bin> <old.bin> [--ctx N] [--top N]
"""
import sys, os, struct, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def dis_at(flash, addr, n):
    off = addr - FLASH_BASE
    out = []
    c = 0
    for ins in md.disasm(flash[off:off + n * 4], addr):
        out.append("  0x%08x  %-31s %-8s %s" %
                   (ins.address, flash[ins.address - FLASH_BASE:ins.address - FLASH_BASE + ins.size].hex(' '),
                    ins.mnemonic, ins.op_str))
        c += 1
        if c >= n:
            break
    return out


def main(argv):
    new_p, old_p = argv[0], argv[1]
    ctx = 8
    top = 40
    if '--ctx' in argv:
        ctx = int(argv[argv.index('--ctx') + 1])
    if '--top' in argv:
        top = int(argv[argv.index('--top') + 1])

    dn, bn, fn = load(new_p)
    do, bo, fo = load(old_p)
    print("new: %s  hdr=0x%x  flash=%d B (0x%08x..0x%08x)  md5 %s" %
          (os.path.basename(new_p), bn, len(fn), FLASH_BASE, FLASH_BASE + len(fn), hashlib.md5(dn).hexdigest()))
    print("old: %s  hdr=0x%x  flash=%d B (0x%08x..0x%08x)  md5 %s" %
          (os.path.basename(old_p), bo, len(fo), FLASH_BASE, FLASH_BASE + len(fo), hashlib.md5(do).hexdigest()))
    print("size delta: %+d bytes" % (len(fn) - len(fo)))

    n = min(len(fn), len(fo))
    diff = bytearray(n)
    for i in range(n):
        if fn[i] != fo[i]:
            diff[i] = 1
    tail = abs(len(fn) - len(fo))
    print("differing bytes in the common prefix: %d (%.1f%% of %d)" %
          (sum(diff), 100.0 * sum(diff) / n, n))
    print("only in the longer image: %d bytes" % tail)

    # group into regions
    regions = []
    i = 0
    while i < n:
        if diff[i]:
            j = i
            while j < n and (diff[j] or (j + 64 < n and any(diff[j:j + 64]))):
                j += 1
            regions.append((i, j))
            i = j
        else:
            i += 1
    regions = [r for r in regions if r[1] - r[0] >= 4]
    print("changed regions (>=4 B): %d" % len(regions))
    print()
    print("=== changed regions, largest first ===")
    for a, b in sorted(regions, key=lambda r: r[0] - r[1], reverse=True)[:top]:
        print("  file 0x%06x..0x%06x  flash 0x%08x..0x%08x  (%d B)" %
              (a, b, FLASH_BASE + a, FLASH_BASE + b, b - a))

    print()
    print("=== first 6 regions with context disassembly ===")
    for a, b in regions[:6]:
        addr = FLASH_BASE + a
        print("-" * 100)
        print("### change at flash 0x%08x..0x%08x (%d B)" % (addr, FLASH_BASE + b, b - a))
        start = FLASH_BASE + max(0, a - ctx * 4)
        print("--- OLD (3.1.5-style) ---")
        for line in dis_at(fo, start, (b - a) // 2 + ctx * 2 + 4):
            print(line)
        print("--- NEW ---")
        for line in dis_at(fn, start, (b - a) // 2 + ctx * 2 + 4):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
