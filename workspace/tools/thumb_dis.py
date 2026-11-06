"""thumb_dis.py - small Thumb-2 disassembler / listing helper for servo images.

Wraps capstone with the conventions this firmware uses:
  * image mapped at 0x08000000
  * call targets are Thumb (bit0 of the target is the state bit)
  * BL / BLX and PC-relative literal loads are annotated with the resolved value

usage:
  python tools\\thumb_dis.py <flash.bin> --at 0x08004400 --len 0x140
  python tools\\thumb_dis.py <flash.bin> --func 0x08004438          # until return/padding
  python tools\\thumb_dis.py <flash.bin> --xref 0x080048d0          # who branches here
  python tools\\thumb_dis.py <flash.bin> --xref-lit 0x080044cc      # who loads this literal
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


def dis(flash, addr, ln, cs_arch, cs):
    o = addr - FLASH_BASE
    code = flash[o:o + ln]
    for ins in cs.Cs(CS_ARCH, CS_MODE) if False else []:
        pass


def main(argv):
    path = argv[0]
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    except ImportError:
        raise SystemExit("needs capstone: pip install capstone")

    _d, _hdr, flash = load(path)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = False

    def resolve_lit(addr, ln):
        vals = {}
        for i in md.disasm(flash[addr - FLASH_BASE:addr - FLASH_BASE + ln],
                           addr):
            if i.mnemonic == 'ldr' and 'pc' in i.op_str:
                try:
                    off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                except ValueError:
                    continue
                pc = (i.address + 4) & ~3
                tgt = pc + off
                if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                    v = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                    vals[i.address] = (tgt, v)
        return vals

    if '--xref-lit' in argv:
        want = int(argv[argv.index('--xref-lit') + 1], 16)
        print("=== who loads the literal word 0x%08x ===" % want)
        # the literal itself
        o = want - FLASH_BASE
        if 0 <= o <= len(flash) - 4:
            print("  word at 0x%08x = 0x%08x" % (want, struct.unpack_from('<I', flash, o)[0]))
        # scan every ldr rX,[pc,#n] in the image
        hits = 0
        step = 2
        for a in range(FLASH_BASE, FLASH_BASE + len(flash) - 4, step):
            for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
                if i.mnemonic == 'ldr' and 'pc' in i.op_str:
                    try:
                        off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                    except ValueError:
                        break
                    pc = (i.address + 4) & ~3
                    if pc + off == want:
                        print("    %08x: %-8s %s" % (i.address, i.mnemonic, i.op_str))
                        hits += 1
                break
        print("  %d referencing site(s)" % hits)
        return 0

    if '--xref' in argv:
        want = int(argv[argv.index('--xref') + 1], 16) & ~1
        print("=== who branches/calls 0x%08x ===" % want)
        hits = 0
        for a in range(FLASH_BASE, FLASH_BASE + len(flash) - 4, 2):
            for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
                if i.mnemonic in ('bl', 'blx', 'b', 'b.w', 'bx') and i.op_str.startswith('#'):
                    try:
                        t = int(i.op_str[1:], 0) & ~1
                    except ValueError:
                        break
                    if t == want:
                        print("    %08x: %-8s %s" % (i.address, i.mnemonic, i.op_str))
                        hits += 1
                break
        print("  %d site(s)" % hits)
        return 0

    at = int(argv[argv.index('--at') + 1], 16) if '--at' in argv else None
    ln = int(argv[argv.index('--len') + 1], 16) if '--len' in argv else 0x100
    if '--func' in argv:
        at = int(argv[argv.index('--func') + 1], 16)
        ln = 0x400
    if at is None:
        raise SystemExit("need --at/--len, --func, --xref or --xref-lit")

    lits = resolve_lit(at, ln)
    print("=== 0x%08x..0x%08x ===" % (at, at + ln))
    for i in md.disasm(flash[at - FLASH_BASE:at - FLASH_BASE + ln], at):
        note = ""
        if i.address in lits:
            tgt, v = lits[i.address]
            note = "   ; lit@0x%08x = 0x%08x" % (tgt, v)
        if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
            note += "   ; -> 0x%08x" % (int(i.op_str[1:], 0) & ~1)
        print("  %08x: %-8s %-28s%s" % (i.address, i.mnemonic, i.op_str, note))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
