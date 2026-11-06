"""od_refs2.py - find the code that READS given literal-pool addresses.

Given a literal address L (e.g. one holding a pointer into the OD table), find
the Thumb `ldr rX, [pc, #n]` whose effective address is exactly L, then print
the surrounding instructions.  That code is the consumer of the descriptor.

usage: python tools\\od_refs2.py <flash.bin> <lit_addr_hex> [<lit_addr_hex> ...] [--ctx N]
"""
import sys, os, struct, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def ldr_pc_refs(flash):
    """[(ins_addr, literal_addr)] for every ldr rX,[pc,#n]"""
    out = []
    md.skipdata = True
    for ins in md.disasm(flash, FLASH_BASE):
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
            mt = re.search(r'#(-?0x[0-9a-fA-F]+|-?\d+)', ins.op_str)
            if mt:
                lit = ((ins.address + 4) & ~1) + int(mt.group(1), 0)
                out.append((ins.address, lit, ins.op_str))
    return out


def show(flash, addr, before, after):
    lo = max(FLASH_BASE, addr - before)
    hi = addr + after
    md.skipdata = True
    for ins in md.disasm(flash[lo - FLASH_BASE:hi - FLASH_BASE], lo):
        mark = "  <<<" if ins.address == addr else ""
        print("     0x%08x  %-30s %-8s %s%s" %
              (ins.address, flash[ins.address - FLASH_BASE:ins.address - FLASH_BASE + ins.size].hex(' '),
               ins.mnemonic, ins.op_str, mark))


def main(argv):
    path = argv[0]
    lits = []
    ctx = 0x14
    for a in argv[1:]:
        if a == '--ctx':
            continue
        if re.fullmatch(r'0x[0-9a-fA-F]+', a):
            lits.append(int(a, 16))
    if '--ctx' in argv:
        ctx = int(argv[argv.index('--ctx') + 1], 16)
    _d, _h, flash = load(path)
    refs = ldr_pc_refs(flash)
    print("%s: %d ldr-from-literal sites" % (os.path.basename(path), len(refs)))
    for L in lits:
        hits = [(a, o) for a, l, o in refs if l == L]
        val = struct.unpack_from('<I', flash, L - FLASH_BASE)[0] if FLASH_BASE <= L < FLASH_BASE + len(flash) - 4 else None
        print()
        print("=== literal 0x%08x (holds 0x%08x): %d reader(s) ===" %
              (L, val if val is not None else 0, len(hits)))
        for a, o in hits[:3]:
            print("   read by 0x%08x  (%s)" % (a, o))
            show(flash, a, ctx, ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
