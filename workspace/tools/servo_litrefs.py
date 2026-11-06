"""servo_litrefs.py - find every instruction that loads a given absolute address from a
PC-relative literal pool, and show the surrounding context.

Why: the position-value write chain turned up two RAM symbols whose role is unknown -
a byte flag at 0x20000022 and a global at 0x20003DB0 - plus the function-pointer tables
the position value flows through.  To place a symbol we need its readers/writers, and
the reliable way to find those is to resolve every literal-pool load and compare the
loaded VALUE (not the address of the literal), because this firmware builds 32-bit
constants via literal pools rather than movw/movt (see SERVO_POSCHAIN_FINDING.md).

usage:
  python tools\\servo_litrefs.py <flash.bin> --lit 0x20000022
  python tools\\servo_litrefs.py <flash.bin> --lit 0x20003db0 --ctx 6 --compare <other.bin>
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


def scan(md, flash, lit, ctx):
    """Return list of (site_addr, [context instruction strings])."""
    out = []
    n = len(flash)
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 4:
        ms = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if not ms:
            a += 2
            continue
        i = ms[0]
        if i.mnemonic == 'ldr' and 'pc' in i.op_str:
            try:
                off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + n - 4:
                    val = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                    if val == lit:
                        body = []
                        for k in md.disasm(flash[i.address - FLASH_BASE + i.size:
                                                i.address - FLASH_BASE + i.size + 6 * ctx],
                                           i.address + i.size):
                            body.append((k.address, k.mnemonic, k.op_str))
                        out.append((i.address, i.op_str, body))
            except (ValueError, IndexError):
                pass
        a += i.size
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    lit = int(argv[argv.index('--lit') + 1], 16)
    ctx = int(argv[argv.index('--ctx') + 1]) if '--ctx' in argv else 5

    for tag, path in (('A', argv[0]),):
        flash = load(path)[2]
        hits = scan(md, flash, lit, ctx)
        print("### %s    literal value 0x%08X   -> %d load site(s)" % (path, lit, len(hits)))
        for a, ops, body in hits:
            print("  0x%08x  ldr %s" % (a, ops))
            for ba, bm, bo in body:
                print("        0x%08x  %-9s %s" % (ba, bm, bo))
            print()

    if '--compare' in argv:
        other = argv[argv.index('--compare') + 1]
        f2 = load(other)[2]
        h2 = scan(md, f2, lit, ctx)
        print("### %s : %d load site(s)" % (other, len(h2)))
        for a, ops, body in h2:
            print("  0x%08x  ldr %s" % (a, ops))
            for ba, bm, bo in body:
                print("        0x%08x  %-9s %s" % (ba, bm, bo))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
