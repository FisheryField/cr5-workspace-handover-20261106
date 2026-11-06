"""servo_sdiff.py - compare the printable-string inventories of two firmware
builds.  String-table deltas are the cheapest high-signal evidence of what a
release changed (new features, new objects, new error paths).

usage: python tools\\servo_sdiff.py <new.bin> <old.bin> [--min N] [--kw word]
"""
import sys, os, struct, re, collections, hashlib

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def strings(flash, minlen):
    out = collections.Counter()
    for mt in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, flash):
        out[mt.group().decode('ascii')] += 1
    return out


def main(argv):
    new_p, old_p = argv[0], argv[1]
    minlen = int(argv[argv.index('--min') + 1]) if '--min' in argv else 6
    kw = argv[argv.index('--kw') + 1].lower() if '--kw' in argv else None
    _dn, _bn, fn = load(new_p)
    _do, _bo, fo = load(old_p)
    sn, so = strings(fn, minlen), strings(fo, minlen)
    print("new %s: %d distinct strings (>=%d chars)" % (os.path.basename(new_p), len(sn), minlen))
    print("old %s: %d distinct strings" % (os.path.basename(old_p), len(so)))
    only_new = sorted(set(sn) - set(so))
    only_old = sorted(set(so) - set(sn))
    both = len(set(sn) & set(so))
    print("common %d ; only in new %d ; only in old %d" % (both, len(only_new), len(only_old)))
    print()
    if kw:
        print("=== strings containing %r in NEW ===" % kw)
        for s in sorted(sn):
            if kw in s.lower():
                print("   %r" % s)
        print()
        print("=== strings containing %r in OLD ===" % kw)
        for s in sorted(so):
            if kw in s.lower():
                print("   %r" % s)
        return 0
    print("=== only in NEW (%d, showing up to 120) ===" % len(only_new))
    for s in only_new[:120]:
        print("   + %r" % s)
    print()
    print("=== only in OLD (%d, showing up to 60) ===" % len(only_old))
    for s in only_old[:60]:
        print("   - %r" % s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
