#!/usr/bin/env python3
"""Compare two builds' *field-copy series* instruction by instruction.

Motivation (this session): D8 0x080214F0.. and 3150 0x0802005C.. are the same
long straight-line block that copies source fields (relative to r5) into an
object (relative to r4).  Reading it in fragments produced contradictory
conclusions:
  * spots +0x2c and +0xCC showed 3150 = D8 + 8
  * +0x50..+0x78 showed 3150 == D8 exactly
  * +0x7c showed 3150 = D8 + 4
Spot-checking cannot resolve this.  So: normalise every instruction, strip the
*absolute* address operands (PC-relative literals and branch targets move
between builds), then align the two sequences.

Output: aligned table with MATCH / DIFF, so the real structural differences are
visible at once.

Usage:
  servo_copyseq.py <A.bin> <B.bin> --a 0x080214F0 --b 0x0802005C --len 0x200
"""
import argparse
import re
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

from servo_img import FLASH_BASE as BASE, load_image


def load(p):
    """Return header-stripped flash image (see servo_img: the .bin files carry a
    ~0x20 byte vendor header, so raw offsets must not be used directly)."""
    return load_image(p)[2]


def dis(data, at, size):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    return list(md.disasm(data[at - BASE:at - BASE + size], at))


# operands that legitimately move between builds -> must be normalised away
def norm(ins):
    m, o = ins.mnemonic, ins.op_str
    # capstone appends "; lit@0x... = 0x20007224" to PC-relative loads; the
    # resolved *address* always moves between builds, so drop the comment or
    # every literal load shows up as a spurious A-only/B-only pair.
    o = o.split(";")[0].strip()
    # PC-relative literal pool offset / absolute branch target
    o = re.sub(r"#0x08[0-9a-f]{6}", "#ADDR", o)
    return m, o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--a", dest="at_a", required=True)
    ap.add_argument("--b", dest="at_b", required=True)
    ap.add_argument("--len", default="0x200")
    args = ap.parse_args()

    size = int(args.len, 16)
    ia = dis(load(args.a), int(args.at_a, 16), size)
    ib = dis(load(args.b), int(args.at_b, 16), size)

    print("A: %d insns from %s" % (len(ia), args.at_a))
    print("B: %d insns from %s" % (len(ib), args.at_b))
    print()

    # align by index but re-sync when a normalised pair fails, so an inserted
    # instruction does not smear the whole rest of the listing
    i = j = 0
    diffs = 0
    while i < len(ia) and j < len(ib):
        na, nb = norm(ia[i]), norm(ib[j])
        if na == nb:
            print("  %08x %-10s %-26s | %08x %-10s %s"
                  % (ia[i].address, na[0], na[1], ib[j].address, nb[0], nb[1]))
            i += 1
            j += 1
            continue

        # try to re-sync: scan a small window for a match
        resync = None
        for da in range(0, 5):
            for db in range(0, 5):
                if da == 0 and db == 0:
                    continue
                if i + da < len(ia) and j + db < len(ib) and norm(ia[i + da]) == norm(ib[j + db]):
                    resync = (da, db)
                    break
            if resync:
                break

        diffs += 1
        if resync:
            da, db = resync
            for k in range(da):
                print("  %08x %-10s %-26s | %-8s %-10s <== A-only"
                      % (ia[i + k].address, norm(ia[i + k])[0], norm(ia[i + k])[1], "-", "-"))
            for k in range(db):
                print("  %-8s %-10s %-26s | %08x %-10s %s <== B-only"
                      % ("-", "-", "-", ib[j + k].address, norm(ib[j + k])[0], norm(ib[j + k])[1]))
            i += da
            j += db
        else:
            print("!! UNRESYNCED  A %08x %s %s   vs   B %08x %s %s"
                  % (ia[i].address, na[0], na[1], ib[j].address, nb[0], nb[1]))
            i += 1
            j += 1

    print()
    print("divergence events: %d   (A insns left: %d, B insns left: %d)"
          % (diffs, len(ia) - i, len(ib) - j))
    return 0


if __name__ == "__main__":
    sys.exit(main())
