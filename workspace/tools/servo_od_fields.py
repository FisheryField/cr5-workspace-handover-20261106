"""servo_od_fields.py - extract the full field-offset map of the OD access service.

The 0x6064 handler in firmware 3.2.D.8 resolves an object as

    ptr = [0x2000138C] + subIndex*0x329 + FIELD_OFFSET
    str ptr,[r0,#0x18]

and every handler in the service uses the same shape with a different FIELD_OFFSET.
Collecting those offsets gives the object-internal layout - i.e. which byte ranges
hold which members - without needing the RAM array itself.

It also reports, per field offset, the CiA402 index (if any) that the dispatcher
routes to it, where that can be determined from the compare chain + jumps.

usage:
  python tools\\servo_od_fields.py <flash.bin> [--lo 0x08002a00] [--hi 0x08003000]
"""
import sys, struct, collections

FLASH_BASE = 0x08000000
STAGING_LIT = 0x08002e58      # literal pool slot holding [0x2000138C]


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
    lo = int(argv[argv.index('--lo') + 1], 16) if '--lo' in argv else 0x08002a00
    hi = int(argv[argv.index('--hi') + 1], 16) if '--hi' in argv else 0x08003300

    listing = list(md.disasm(flash[lo - FLASH_BASE:hi - FLASH_BASE], lo))

    # find literal-pool slots holding the base pointer
    base_lits = set()
    for o in range(lo - FLASH_BASE, hi - FLASH_BASE - 4, 4):
        if struct.unpack_from('<I', flash, o)[0] == 0x2000138C:
            base_lits.add(FLASH_BASE + o)
    print("literal pool slot(s) holding 0x2000138C in scan window: %s" %
          [hex(x) for x in sorted(base_lits)])

    # walk: movw r,#0x329 ; muls ; ldr rX,[pc,#n] -> base ; add ; add #off ; str [r0,#0x18]
    fields = []
    for i, ins in enumerate(listing):
        if ins.mnemonic == 'str' and 'r0, #0x18' in ins.op_str:
            off = None
            base = None
            for j in range(max(0, i - 8), i):
                pj = listing[j]
                if pj.mnemonic.startswith('add') and '#' in pj.op_str:
                    try:
                        cand = int(pj.op_str.split('#')[-1], 0)
                    except ValueError:
                        continue
                    if cand and cand != 0x329:
                        off = cand
                if pj.mnemonic == 'ldr' and 'pc' in pj.op_str:
                    try:
                        n = int(pj.op_str.split('#')[-1].rstrip(']'), 0)
                    except ValueError:
                        continue
                    tgt = ((pj.address + 4) & ~3) + n
                    if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                        v = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                        if v == 0x2000138C:
                            base = pj.address
            if off is not None and base is not None:
                fields.append((ins.address, off))

    print("\n=== (str [r0,#0x18] site, object field offset) ===")
    for a, off in fields:
        print("  0x%08x  field +0x%03x  (%d)" % (a, off, off))

    c = collections.Counter(off for _a, off in fields)
    print("\n=== offset histogram (n=%d sites) ===" % len(fields))
    for off, n in sorted(c.items()):
        print("  +0x%03x : %d" % (off, n))

    print("\n=== contiguous runs of 2-byte-spaced offsets (likely array members) ===")
    offs = sorted(c)
    run = [offs[0]] if offs else []
    for v in offs[1:]:
        if v - run[-1] == 2:
            run.append(v)
        else:
            if len(run) >= 3:
                print("  +0x%03x .. +0x%03x  (%d members)" % (run[0], run[-1], len(run)))
            run = [v]
    if len(run) >= 3:
        print("  +0x%03x .. +0x%03x  (%d members)" % (run[0], run[-1], len(run)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
