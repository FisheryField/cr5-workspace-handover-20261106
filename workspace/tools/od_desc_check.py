"""od_desc_check.py - test the "6 literal dwords point into the OD table" claim.

SERVO_FW_OD_FINDING.md sections 4.1 / 7.1 claim that exactly six 32-bit literals in
the whole image point into the OD metadata table (0x08024991..0x0802642e):

    0x080513cc -> 0x08024945    0x080513f4 -> 0x08024d15
    0x08052520 -> 0x08025f39    0x080527a4 -> 0x08025eed
    0x080527a8 -> 0x08025f11    0x080527b4 -> 0x08025991

and that those targets are NOT the start of an entry (they land inside a name
string), so the table must be indexed by offset.

This script re-derives that from the binary instead of trusting the note:

  1. print the bytes at each target and the enclosing printable run
  2. print the decoded 6-byte descriptors at each target
  3. scan the whole image for ALL dwords pointing into the table and report
     how many there are and where

usage:
  python tools\\od_desc_check.py <flash.bin>
"""
import sys, struct, re

FLASH_BASE = 0x08000000
TABLE_LO = 0x08024991
TABLE_HI = 0x0802642e
TARGETS = {
    0x080513cc: 0x08024945, 0x080513f4: 0x08024d15,
    0x08052520: 0x08025f39, 0x080527a4: 0x08025eed,
    0x080527a8: 0x08025f11, 0x080527b4: 0x08025991,
}
TYPE = {0x02: 'i8', 0x03: 'i16', 0x04: 'i32', 0x05: 'u8', 0x06: 'u16', 0x07: 'u32'}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def enclosing(flash, addr):
    """Printable run (string) containing addr, plus its bounds."""
    o = addr - FLASH_BASE
    s = o
    while s > 0 and 0x20 <= flash[s - 1] < 0x7f:
        s -= 1
    e = o
    while e < len(flash) and 0x20 <= flash[e] < 0x7f:
        e += 1
    run = flash[s:e]
    return FLASH_BASE + s, FLASH_BASE + e, run.decode('ascii', 'replace'), o - s


def desc(flash, addr, n=3):
    o = addr - FLASH_BASE
    out = []
    for i in range(n):
        b = flash[o + 6 * i:o + 6 * i + 6]
        if len(b) < 6:
            break
        t, th, bits, bh, a, ah = b
        ok = th == 0 and bh == 0 and ah == 0 and t in TYPE and bits in (8, 16, 32)
        out.append("%s -> %s/%d/a=0x%02x" % (b.hex(' '),
                   TYPE.get(t, '?%02x' % t) if ok else 'INVALID', bits, a))
    return out


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    print("table = 0x%08x..0x%08x" % (TABLE_LO, TABLE_HI))

    print("\n=== the 6 claimed (literal -> target) pairs ===")
    for lit in sorted(TARGETS):
        tgt = TARGETS[lit]
        # confirm the literal really holds tgt
        o = lit - FLASH_BASE
        if 0 <= o <= len(flash) - 4:
            actual = struct.unpack_from('<I', flash, o)[0]
        else:
            actual = None
        s, e, name, off = enclosing(flash, tgt)
        mark = "MID-STRING" if off > 0 else "at-string-start"
        print("\n  literal 0x%08x holds 0x%08x  %s" %
              (lit, actual or 0, "OK" if actual == tgt else "MISMATCH!"))
        print("    target 0x%08x -> run 0x%08x..0x%08x (%s, offset +%d in run)" %
              (tgt, s, e, mark, off))
        print("    run = %r" % name)
        for d in desc(flash, tgt):
            print("      %s" % d)

    print("\n=== exhaustive scan: every dword in the image pointing into the table ===")
    hits = []
    for o in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if TABLE_LO <= v < TABLE_HI:
            hits.append((FLASH_BASE + o, v))
    print("  found %d" % len(hits))
    for a, v in hits:
        s, e, name, off = enclosing(flash, v)
        print("    0x%08x -> 0x%08x  run=%-34r +%d" % (a, v, name[:34], off))

    print("\n=== same scan, 2-byte aligned (catch byte-packed tables) ===")
    hits2 = []
    for o in range(0, len(flash) - 4, 2):
        v = struct.unpack_from('<I', flash, o)[0]
        if TABLE_LO <= v < TABLE_HI:
            hits2.append((FLASH_BASE + o, v))
    print("  found %d (vs %d on 4-byte grid)" % (len(hits2), len(hits)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
