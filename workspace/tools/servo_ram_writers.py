"""servo_ram_writers.py - find code that WRITES to a RAM address range in the servo
image, including stores made through a PC-relative-loaded base register.

Why this is needed: the non-volatile save routine appends a 16-byte payload read from
RAM 0x200096E8 to a flash log.  Finding the code that POPULATES 0x200096E8 tells us
what actually gets persisted - which is the question that decides whether the zero
offset is in there.

Naive literal-dword scanning misses writes made through a struct pointer, so this
script instead looks for the two direct forms compiler output uses:

  A) `ldr rX,[pc,#n]`   -> literal holds a RAM address in range, followed within a
     few instructions by `str/strb/strh rY,[rX,#off]`            (direct global store)
  B) `str/strb/strh rY,[rX,#off]` where rX was set up earlier in the same function
     from a literal in range                                    (struct field store)

It reports, per site, the resolved base address, the store offset, so the exact
target address is known.

usage:
  python tools\\servo_ram_writers.py <flash.bin> --lo 0x200096e8 --hi 0x20009708
  python tools\\servo_ram_writers.py <flash.bin> --lo 0x20009600 --hi 0x20009800
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
    lo = int(argv[argv.index('--lo') + 1], 16)
    hi = int(argv[argv.index('--hi') + 1], 16)

    # Build an instruction map once (address -> (mnemonic, op_str)).
    insns = {}
    a = FLASH_BASE
    while a <= FLASH_BASE + len(flash) - 4:
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            insns[a] = (i.mnemonic, i.op_str)
            break
        a += 2

    def lit_of(addr):
        """If instruction at addr is ldr rX,[pc,#n], return the loaded dword."""
        if addr not in insns:
            return None
        mn, ops = insns[addr]
        if mn != 'ldr' or 'pc' not in ops:
            return None
        try:
            off = int(ops.split('#')[-1].rstrip(']'), 0)
        except ValueError:
            return None
        tgt = ((addr + 4) & ~3) + off
        if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
            return struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
        return None

    print("scanning writers into 0x%08x..0x%08x" % (lo, hi))
    found = []

    for a in sorted(insns):
        mn, ops = insns[a]
        if not mn.startswith('str'):
            continue
        # str rY,[rX]  or  str rY,[rX,#off]
        if '[' not in ops:
            continue
        inside = ops[ops.index('[') + 1:ops.index(']')]
        parts = [p.strip() for p in inside.split(',')]
        base_reg = parts[0]
        off = 0
        if len(parts) > 1 and parts[1].startswith('#'):
            try:
                off = int(parts[1][1:], 0)
            except ValueError:
                off = 0
        # (B) scan back up to 12 instructions for the setup of base_reg
        for back in range(2, 26, 2):
            pa = a - back
            if pa not in insns:
                continue
            pmn, pops = insns[pa]
            if pmn == 'ldr' and pops.startswith(base_reg + ',') and 'pc' in pops:
                v = lit_of(pa)
                if v is not None and lo <= v + off < hi:
                    found.append((a, base_reg, off, v, v + off, pmn))
                break
            if pmn in ('add', 'add.w', 'adds') and pops.startswith(base_reg + ','):
                # add rX, rY, #imm  - base is rY; check rY setup
                continue

    seen = set()
    print("\n=== store sites resolved to the region ===")
    for a, reg, off, v, tgt, _pm in found:
        if (a, tgt) in seen:
            continue
        seen.add((a, tgt))
        mn, ops = insns[a]
        print("  0x%08x  %-6s %-22s  base=0x%08x off=0x%-3x -> 0x%08x" %
              (a, mn, ops, v, off, tgt))
    print("  %d distinct store site(s)" % len(seen))

    if not seen:
        print("  (none - the payload is probably filled through a struct pointer whose")
        print("   base is passed in as an argument; widen --lo/--hi or search the")
        print("   enclosing RAM object instead)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
