"""servo_cmp_region.py - side-by-side disassembly of one flash region in two
builds, so the shared/divergent code can actually be read.

usage: python tools\\servo_cmp_region.py <new.bin> <old.bin> <addr> <len> [--diff-only]
"""
import sys, os, struct

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


def list_dis(flash, addr, ln):
    o = addr - FLASH_BASE
    out = []
    md.skipdata = True
    for ins in md.disasm(flash[o:o + ln], addr):
        out.append((ins.address, ins.size,
                    flash[ins.address - FLASH_BASE:ins.address - FLASH_BASE + ins.size].hex(' '),
                    ins.mnemonic, ins.op_str))
    return out


def main(argv):
    new_p, old_p = argv[0], argv[1]
    addr = int(argv[2], 16)
    ln = int(argv[3], 16)
    diff_only = '--diff-only' in argv
    _dn, _bn, fn = load(new_p)
    _do, _bo, fo = load(old_p)
    A = list_dis(fn, addr, ln)
    B = list_dis(fo, addr, ln)

    # index by address
    bmap = {a: (s, h, m, o) for a, s, h, m, o in B}
    print("=" * 104)
    print("flash 0x%08x..0x%08x   (# same bytes)" % (addr, addr + ln))
    print("%-28s | %-28s" % ("NEW 3.2.D.8", "OLD 3.1.5.0"))
    print("=" * 104)
    shown = 0
    for a, s, h, m, o in A:
        b = bmap.get(a)
        if b is None:
            continue
        bs, bh, bm, bo = b
        same = (h == bh)
        if diff_only and same:
            continue
        mark = " " if same else "*"
        print("%s0x%08x %-23s | 0x%08x %-23s" % (mark, a, (m + ' ' + o)[:23], a, (bm + ' ' + bo)[:23]))
        shown += 1
    print()
    print("%d instruction rows shown (mark * = bytes differ)" % shown)

    # byte-level identity summary of the region
    o = addr - FLASH_BASE
    n = min(ln, len(fn) - o, len(fo) - o)
    sameb = sum(1 for i in range(n) if fn[o + i] == fo[o + i])
    print("byte identity in region: %d/%d = %.1f%%" % (sameb, n, 100.0 * sameb / n))
    # longest identical run
    best = cur = 0
    bs_ = be_ = 0
    for i in range(n):
        if fn[o + i] == fo[o + i]:
            cur += 1
            if cur > best:
                best = cur
                be_ = i + 1
                bs_ = i + 1 - cur
        else:
            cur = 0
    if best:
        print("longest identical byte run: %d B at 0x%08x..0x%08x" %
              (best, addr + bs_, addr + be_))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
