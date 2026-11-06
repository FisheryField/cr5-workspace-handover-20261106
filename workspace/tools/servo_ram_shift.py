"""servo_ram_shift.py - resolve an address in image A to its counterpart in image B.

Problem this solves (and a recurring source of wrong conclusions in this investigation):

The two servo firmware builds use DIFFERENT RAM addresses for the same objects.
Measured examples:

    position object descriptor base   0x2000138C (3.2.D.8)   0x2000129C (3.1.5.0)   -0xF0
    flag/state struct base            0x200016B5 (3.2.D.8)   0x2000129C?            ...
    D8 literal 0x200015C5 <-> 0x2000129C? 

Naively searching for D8's address in B returns "absent", which several earlier steps in
this investigation mis-read as "the feature does not exist in B".  A negative is only
meaningful once the address has been TRANSLATED.

Method: derive the shift empirically.
  * take the block of RAM literals used by image A (4-byte literals in 0x20000000..)
  * do the same for image B
  * the correct translation T minimises the distance between the two sets, i.e. find the
    T that maps the most A-literals onto B-literals

Then report, for a requested A address, the inferred B address and the evidence.

usage:
  python tools\\servo_ram_shift.py <a.bin> <b.bin> [--at 0x200016b5]
"""
import sys, struct
import collections

FLASH_BASE = 0x08000000
RAM_LO, RAM_HI = 0x20000000, 0x20050000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def ram_literals(flash):
    s = set()
    for o in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if RAM_LO <= v < RAM_HI:
            s.add(v)
    return s


def main(argv):
    A = load(argv[0])[2]
    B = load(argv[1])[2]
    sa, sb = ram_literals(A), ram_literals(B)
    print("RAM literals: A=%d distinct, B=%d distinct" % (len(sa), len(sb)))

    # score candidate shifts
    cand = collections.Counter()
    sbl = sorted(sb)
    setb = sb
    for v in sorted(sa):
        for w in sbl:
            d = v - w
            if -0x4000 <= d <= 0x4000:
                cand[d] += 1
    print("\n=== candidate shifts A-B (top 12) ===")
    for d, n in cand.most_common(12):
        print("  %+6d (0x%+x) : %d A-literals land on a B-literal" % (d, d, n))

    best = cand.most_common(1)[0][0] if cand else 0
    print("\n  best shift = %+d (0x%+x)" % (best, best))

    if '--at' in argv:
        a = int(argv[argv.index('--at') + 1], 16)
        b = a - best
        print("\n  A 0x%08x  ->  B 0x%08x" % (a, b))
        print("    A has literal: %s" % ('yes' if a in sa else 'no'))
        print("    B has literal: %s" % ('yes' if b in sb else 'no'))
        # nearest neighbours on each side, to show the local layout
        near_a = sorted(x for x in sa if abs(x - a) <= 0x40)
        near_b = sorted(x for x in sb if abs(x - b) <= 0x40)
        print("    A neighbours: %s" % ' '.join('0x%x' % x for x in near_a))
        print("    B neighbours: %s" % ' '.join('0x%x' % x for x in near_b))
        if near_a and near_b:
            print("    pair-wise A->B: %s" %
                  ', '.join('0x%x->0x%x' % (x, x - best) for x in near_a[:10]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
