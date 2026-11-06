"""od_refs.py - find the code that walks the object-dictionary metadata table.

The OD table (see od_table.py) holds *metadata only*: no parameter address, no
object index.  Something must map a table entry to the manufacturer parameter
address, so this looks for immediate operands / literal-pool words that point
into the table, and reports the surrounding instruction.

usage: python tools\\od_refs.py <flash.bin> --lo 0x08024900 --hi 0x08026500
"""
import sys, os, struct, re, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)
md.detail = True


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    path = argv[0]
    lo = int(argv[argv.index('--lo') + 1], 16)
    hi = int(argv[argv.index('--hi') + 1], 16)
    _d, _h, flash = load(path)
    print("%s  table range 0x%08x..0x%08x" % (os.path.basename(path), lo, hi))

    # 1) literal-pool words that point into the table
    words = []
    for off in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, off)[0]
        if lo <= v < hi:
            words.append((FLASH_BASE + off, v))
    print("  literal/table words pointing into the OD table: %d" % len(words))
    for a, v in words[:20]:
        print("     0x%08x -> 0x%08x" % (a, v))

    # 2) immediate operands equal to a table address (movw/movt pairs, adds)
    imm = []
    md.skipdata = True
    for ins in md.disasm(flash, FLASH_BASE):
        for op in ins.operands:
            if op.type == 2 and lo <= (op.imm & 0xffffffff) < hi:
                imm.append((ins.address, ins.mnemonic, ins.op_str, op.imm))
                break
    print("  immediate operands inside the table: %d" % len(imm))
    for a, m, s, v in imm[:20]:
        print("     0x%08x  %-8s %s" % (a, m, s))

    # 3) movw/movt pairs that build an address in the table
    pairs = []
    pend = {}
    for ins in md.disasm(flash, FLASH_BASE):
        if ins.mnemonic == 'movw' or ins.mnemonic == 'mov.w':
            mt = re.match(r'(r\d+), #(0x[0-9a-f]+|\d+)', ins.op_str)
            if mt:
                pend[mt.group(1)] = (ins.address, int(mt.group(2), 0))
        elif ins.mnemonic == 'movt':
            mt = re.match(r'(r\d+), #(0x[0-9a-f]+|\d+)', ins.op_str)
            if mt and mt.group(1) in pend:
                a0, v0 = pend.pop(mt.group(1))
                v = v0 | (int(mt.group(2), 0) << 16)
                if lo <= v < hi:
                    pairs.append((a0, ins.address, v))
    print("  movw/movt pairs building a table address: %d" % len(pairs))
    for a0, a1, v in pairs[:20]:
        print("     0x%08x/0x%08x -> 0x%08x" % (a0, a1, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
