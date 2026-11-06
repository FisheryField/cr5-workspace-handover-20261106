"""servo_cg.py - align two firmware builds by their *call graph*, which is far
more robust than trying to recover exact function boundaries from a flat image.

Idea: at a given flash address A, take the sequence of BL/BLX targets found in
the next N bytes.  Addresses that are the same function in both builds usually
call the same set of helper addresses, even when the surrounding code moved.
Score every old address against the new one by Jaccard similarity of those
target sets and report the matches.

usage: python tools\\servo_cg.py <new.bin> <old.bin> [--win N] [--top N]
"""
import sys, os, struct, re, collections, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)
md.detail = False


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def bl_map(flash, win):
    """address -> frozenset(call targets within `win` bytes)"""
    size = len(flash)
    out = {}
    # collect all BL targets with their own address first
    calls = []
    md.skipdata = True
    for ins in md.disasm(flash, FLASH_BASE):
        if ins.mnemonic in ('bl', 'blx') and ins.op_str.startswith('#'):
            try:
                t = int(ins.op_str[1:], 0) & ~1
            except ValueError:
                continue
            if FLASH_BASE <= t < FLASH_BASE + size:
                calls.append((ins.address, t))
    # window fingerprint at every instruction-aligned address that starts a call
    by_addr = {}
    for a, t in calls:
        by_addr.setdefault(a, []).append(t)
    for a, ts in by_addr.items():
        seq = []
        for a2, t2 in calls:
            if a <= a2 < a + win:
                seq.append(t2)
            if a2 >= a + win:
                break
        out[a] = frozenset(seq)
    return out


def main(argv):
    new_p, old_p = argv[0], argv[1]
    win = int(argv[argv.index('--win') + 1], 0) if '--win' in argv else 0x200
    top = int(argv[argv.index('--top') + 1]) if '--top' in argv else 25
    _dn, _bn, fn = load(new_p)
    _do, _bo, fo = load(old_p)
    print("new %s %d B / old %s %d B" % (os.path.basename(new_p), len(fn),
                                         os.path.basename(old_p), len(fo)))
    cn = bl_map(fn, win)
    co = bl_map(fo, win)
    print("call-site fingerprints: new %d, old %d (window 0x%x)" % (len(cn), len(co), win))

    # index old by fingerprint content
    idx = collections.defaultdict(list)
    for a, s in co.items():
        if len(s) >= 2:
            idx[s].append(a)

    same = 0
    moved = []
    for a, s in cn.items():
        if len(s) < 2:
            continue
        hits = idx.get(s)
        if hits:
            same += 1
            if hits[0] != a:
                moved.append((a, hits[0], len(s)))
    print()
    print("call-sites whose *identical* callee set exists in the other build: %d" % same)
    print("  of those, at the SAME address      : %d" % (same - len(moved)))
    print("  of those, at a DIFFERENT address   : %d (code moved)" % len(moved))
    print()
    print("=== examples of moved call sites (new -> old) ===")
    for a, b, n in sorted(moved, key=lambda t: abs(t[0] - t[1]))[:top]:
        print("   0x%08x -> 0x%08x   (%d callees, delta %+#x)" % (a, b, n, b - a))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
