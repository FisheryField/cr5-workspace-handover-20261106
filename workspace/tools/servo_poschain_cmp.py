"""servo_poschain_cmp.py - layout-independent comparison of the POSITION-FAMILY code
between the two servo firmware images.

Why a special method is needed
------------------------------
Earlier comparisons here were done at fixed addresses (brittle: the two images are laid
out differently - the STM32 HAL is shifted by 0x29C - so fixed-address diffs are
meaningless) or by comparing RAM globals (invalid across builds, see
SERVO_PERSIST_FINDING.md).

The robust method is SIGNATURE SEARCH: define the code shape that identifies the
object-member access, locate every occurrence in each image, and compare the resulting
sets.  That is layout-independent.

Signature (from firmware 3.2.D.8, tools/servo_od_fields.py):

    movw  rX, #0x329       ; OD record stride
    muls  rX, rY, rX       ; * subIndex
    ldr   rZ, [pc, #n]     ; descriptor array base pointer
    add   rX, rZ
    add   rX, #FIELD       ; member offset  <- what we want
    str   rX, [r0, #0x18]

Lessons baked in:
  * use capstone for decoding - hand-rolled Thumb-2 bit unpacking produced WRONG
    results twice in this investigation (movw halfword order, add-immediate fields)
  * do not compare RAM addresses across builds

usage:
  python tools\\servo_poschain_cmp.py <a.bin> <b.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000
STRIDE = 0x329


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def analyse(md, flash):
    """Return [(site, member_offset)] using capstone.

    Note: the member offset must be read by decoding FORWARD from the site, not by
    indexing a pre-collected instruction list.  A linear 2-byte sweep interleaves
    decodings, so the `add.w r3, r3, #FIELD` that follows the stride product gets
    swallowed by a longer instruction decoded from an overlapping address - which is
    exactly what made an earlier version of this function report bogus offsets.
    """
    n = len(flash)
    sites = []
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 8:
        ms = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if not ms or ms[0].mnemonic != 'movw' or '#0x%x' % STRIDE != ms[0].op_str.split(', ')[-1]:
            a += 2
            continue
        # walk forward from here
        off = None
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 0x40], a):
            if i.address == a:
                continue
            if i.mnemonic.startswith('add') and '#' in i.op_str:
                try:
                    v = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                except ValueError:
                    continue
                if v and v != STRIDE:
                    off = v
                    break
        sites.append((a, off))
        a += 2
    return sites


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    res = []
    for path in argv:
        flash, _b, _f = load(path)
        sites = analyse(md, flash)
        res.append((path, sites))

    for path, sites in res:
        offs = [o for _a, o in sites if o is not None]
        print("\n######## %s ########" % path)
        print("  movw rX,#0x%x sites: %d   (with member offset resolved: %d)" %
              (STRIDE, len(sites), len(offs)))
        hist = {}
        for o in offs:
            hist[o] = hist.get(o, 0) + 1
        print("  member-offset histogram (offset: count):")
        for o in sorted(hist):
            print("     +0x%03x : %d" % (o, hist[o]))
        res[res.index((path, sites))] = (path, sites)

    if len(res) == 2 and all(s for _p, s in res):
        print("\n######## comparison ########")
        A = {o for _a, o in res[0][1] if o is not None}
        B = {o for _a, o in res[1][1] if o is not None}
        print("  stride sites        : %d vs %d" % (len(res[0][1]), len(res[1][1])))
        print("  distinct offsets A  : %d" % len(A))
        print("  distinct offsets B  : %d" % len(B))
        print("  only in A (3.2.D.8) : %s" % ' '.join('0x%x' % x for x in sorted(A - B)))
        print("  only in B (3.1.5.0) : %s" % ' '.join('0x%x' % x for x in sorted(B - A)))
        print("  shared              : %d" % len(A & B))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
