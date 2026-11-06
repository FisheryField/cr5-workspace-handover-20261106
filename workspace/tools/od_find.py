"""od_find.py - locate the CiA402 object dictionary name table in a servo
firmware image and find the code that references it.

The firmware contains the human-readable OD names ('Home offset',
'Motor calibration date', 'Encoder increments', ...).  Finding where they live
and who points at them is the entry point for reversing the drive's parameter /
persistence logic.

usage: python tools\\od_find.py <flash.bin> [--names a,b,c] [--xrefs]
"""
import sys, os, struct, re, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)

DEFAULT_NAMES = [
    'Home offset', 'Motor calibration date', 'Encoder increments',
    'Position encoder resolution', 'Facturer_specified1', 'Facturer_specified2',
    'Velocity encoder factor', 'Feed constant', 'Gear ratio',
    'Speed during search for zero', 'Drive manufacturer', 'Device name',
    'Hardware version', 'Drive catalog number', 'Position Offset',
]


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def find_strings(flash, names):
    out = {}
    for nm in names:
        b = nm.encode() + b'\0'
        i = flash.find(b)
        if i >= 0:
            out[nm] = FLASH_BASE + i
    return out


def literal_loads(flash):
    """all (insn_addr, literal_addr, literal_value) for ldr rX,[pc,#n]"""
    out = []
    size = len(flash)
    md.skipdata = True
    for ins in md.disasm(flash, FLASH_BASE):
        if ins.mnemonic in ('ldr', 'ldr.w') and '[pc' in ins.op_str:
            mt = re.search(r'#(-?0x[0-9a-fA-F]+|-?\d+)', ins.op_str)
            if not mt:
                continue
            lit = ((ins.address + 4) & ~1) + int(mt.group(1), 0)
            o = lit - FLASH_BASE
            if 0 <= o <= size - 4:
                out.append((ins.address, lit, struct.unpack_from('<I', flash, o)[0]))
    return out


def main(argv):
    path = argv[0]
    names = DEFAULT_NAMES
    if '--names' in argv:
        names = argv[argv.index('--names') + 1].split(',')
    _d, hdr, flash = load(path)
    print("%s  flash %d B (base 0x%08x)" % (os.path.basename(path), len(flash), FLASH_BASE))
    addr = find_strings(flash, names)
    print()
    print("=== object-dictionary name strings found: %d/%d ===" % (len(addr), len(names)))
    for nm in names:
        a = addr.get(nm)
        print("   %-32s %s" % (nm, ("0x%08x" % a) if a else "NOT FOUND"))
    if not addr:
        return 1

    # are they clustered? that would be the name table
    vals = sorted(addr.values())
    print()
    print("   span 0x%08x..0x%08x (%d B), %d strings" %
          (vals[0], vals[-1], vals[-1] - vals[0], len(vals)))
    gaps = [b - a for a, b in zip(vals, vals[1:])]
    if gaps:
        print("   gap between neighbours: min %d median %d max %d" %
              (min(gaps), sorted(gaps)[len(gaps) // 2], max(gaps)))

    # do other OD-looking strings sit between them? (=> one big table)
    lo, hi = vals[0], vals[-1]
    seg = flash[lo - FLASH_BASE:hi - FLASH_BASE + 64]
    runs = [m.group().decode('ascii', 'replace') for m in re.finditer(rb'[\x20-\x7e]{6,}', seg)]
    print("   printable runs inside the span: %d" % len(runs))

    if '--xrefs' in argv:
        print()
        print("=== code that loads these string addresses ===")
        ld = literal_loads(flash)
        want = {a: nm for nm, a in addr.items()}
        hits = collections.defaultdict(list)
        for ins_a, lit, val in ld:
            if val in want:
                hits[want[val]].append((ins_a, lit))
        for nm in names:
            if nm in hits:
                print("   %-32s <- %s" % (nm, " ".join("0x%08x" % a for a, _ in hits[nm][:6])))
        if not hits:
            print("   (none: the names are referenced indirectly, e.g. via a table of")
            print("    pointers - look for a 32-bit word equal to a name address)")
        print()
        print("=== pointer words equal to a name address (table entries?) ===")
        for nm, a in sorted(addr.items(), key=lambda kv: kv[1]):
            w = struct.pack('<I', a)
            i = flash.find(w)
            locs = []
            while i != -1 and len(locs) < 4:
                locs.append(FLASH_BASE + i)
                i = flash.find(w, i + 1)
            print("   %-32s 0x%08x  ptr from: %s" % (nm, a, " ".join("0x%08x" % x for x in locs) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
