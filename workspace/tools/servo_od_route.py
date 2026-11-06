"""servo_od_route.py - resolve which CiA402 index each OD handler / field offset belongs to.

tools/servo_od_service.py found only 5 `movw` index constants because the dispatcher
is a binary search whose remaining routing happens through `tbb`/`tbh` jump tables.
Without resolving those tables the field-offset map from tools/servo_od_fields.py
cannot be attributed to objects - which is the thing that actually matters for the
zero-point question.

Mechanism (Thumb-2):
  tbb [pc, rN]                 -> 1-byte table, target = pc + 2*entry
  tbh [pc, rN, lsl #1]         -> 2-byte table, target = pc + 2*entry
where `pc` is the address of the tbb/tbh instruction plus 4 (aligned), and the table
bytes/halfwords sit immediately after it.

This script:
  * finds every tbb/tbh in the service region
  * decodes its table and prints the entry targets
  * reports which of those targets are handlers that produce a field offset
    (i.e. contain `str rX,[r0,#0x18]`), so index -> field offset can be assembled

usage:
  python tools\\servo_od_route.py <flash.bin> [--lo 0x0800289c] [--hi 0x08003000]
"""
import sys, struct

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    flash, _b, _f = load(path)
    lo = int(argv[argv.index('--lo') + 1], 16) if '--lo' in argv else 0x0800289c
    hi = int(argv[argv.index('--hi') + 1], 16) if '--hi' in argv else 0x08003000
    print("service region 0x%08x..0x%08x" % (lo, hi))

    listing = list(md.disasm(flash[lo - FLASH_BASE:hi - FLASH_BASE], lo))

    print("\n=== tbb / tbh sites and their decoded tables ===")
    tables = []
    for ins in listing:
        if ins.mnemonic in ('tbb', 'tbh'):
            scale = 1 if ins.mnemonic == 'tbb' else 2
            # PC value used by the table lookup
            pcb = (ins.address + 4) & ~1
            tab = pcb
            n = 16
            ent = []
            for k in range(n):
                o = tab - FLASH_BASE + k * scale
                if o < 0 or o + scale > len(flash):
                    break
                if scale == 1:
                    e = flash[o]
                else:
                    e = struct.unpack_from('<H', flash, o)[0]
                ent.append((k, pcb + 2 * e))
            tables.append((ins.address, ins.mnemonic, tab, ent))
            print("\n  0x%08x %s   table at 0x%08x (n=%d)" % (ins.address, ins.mnemonic, tab, len(ent)))
            for k, t in ent:
                print("      [%2d] -> 0x%08x" % (k, t))

    if not tables:
        print("  (none found in region)")

    # which handler entry points produce a field offset?
    print("\n=== handler entries -> field offset (looks for `str rX,[r0,#0x18]` + preceding add/muls) ===")
    entries = set()
    for _a, _m, _t, ent in tables:
        for _k, t in ent:
            if FLASH_BASE <= t < FLASH_BASE + len(flash):
                entries.add(t)
    # also the direct branch targets found earlier
    for t in (0x08002960, 0x08002962, 0x08002964, 0x08002966, 0x08002968,
              0x0800296a, 0x0800296c, 0x0800296e, 0x08002970):
        entries.add(t)

    resolved = []
    for e in sorted(entries):
        sub = list(md.disasm(flash[e - FLASH_BASE:e - FLASH_BASE + 0x20], e))
        # follow a single `b` to the real body
        body = e
        if sub and sub[0].mnemonic == 'b' and sub[0].op_str.startswith('#'):
            try:
                body = int(sub[0].op_str[1:], 0) & ~1
            except ValueError:
                body = e
        bl = list(md.disasm(flash[body - FLASH_BASE:body - FLASH_BASE + 0x30], body))
        off = None
        stride = False
        for i in bl:
            if i.mnemonic.startswith('add') and '#' in i.op_str:
                try:
                    v = int(i.op_str.split('#')[-1], 0)
                    if 0 < v < 0x329:
                        off = v
                except ValueError:
                    pass
            if i.mnemonic == 'movw' and '0x329' in i.op_str:
                stride = True
        resolved.append((e, body, off, stride))

    print("  %-10s %-10s %-8s %s" % ("entry", "body", "field", "stride0x329"))
    for e, body, off, stride in resolved:
        print("  0x%08x 0x%08x  %-8s %s" %
              (e, body, ('+0x%03x' % off) if off else '-', 'YES' if stride else 'no'))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
