"""servo_marker_find.py - resolve a routine's RAM globals in ANY image by anchoring on
code, not on the address.

Why: tools/servo_nvmap.py compared the two firmware versions by looking for the SAME
literal RAM addresses and reported five as "absent" from v3.1.5.0.  That was a bad
method.  Direct disassembly shows v3.1.5.0 has the SAME persist routine with the same
code shape, but its globals live at different addresses:

    v3.2.D.8   staging copy dst 0x200096E4   flag 0x2000348C   count 0x20003494   wptr 0x20003470
    v3.1.5.0   staging copy dst 0x200091FC   flag 0x20003384   (etc.)

So RAM globals MUST NOT be compared by value across builds - the linker places them
wherever the map allows.  This script resolves them structurally instead:

  * find the persist routine by its 0xA1B2C3D4 magic literal
  * walk outward and record, in program order, every literal-pool RAM address the
    routine actually uses, tagged with the register/role it is loaded into
  * do the same for the API routine that stages parameters
  * print the two images side by side by ROLE, which is layout-independent

usage:
  python tools\\servo_marker_find.py <a.bin> <b.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000
MAGIC_HDR = 0xA1B2C3D4


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def magic_sites(flash, val):
    return [FLASH_BASE + o for o in range(0, len(flash) - 4, 4)
            if struct.unpack_from('<I', flash, o)[0] == val]


def prologue_at_or_before(flash, addr, limit=0x300):
    """Nearest `push {...,lr}` at or before addr."""
    for a in range(addr, max(FLASH_BASE, addr - limit), -2):
        b = flash[a - FLASH_BASE:a - FLASH_BASE + 2]
        if len(b) == 2 and b[1] == 0xB5:
            return a
    return None


def walk(md, flash, head, maxlen=0x200):
    """Return list of (addr, mnemonic, ops, literal_value_or_None)."""
    out = []
    for i in md.disasm(flash[head - FLASH_BASE:head - FLASH_BASE + maxlen], head):
        lit = None
        if i.mnemonic == 'ldr' and 'pc' in i.op_str:
            try:
                off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                    lit = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
            except ValueError:
                pass
        out.append((i.address, i.mnemonic, i.op_str, lit))
        # a return ends the function
        if i.mnemonic.startswith('pop') and 'pc' in i.op_str:
            break
        if i.mnemonic == 'bx' and 'lr' in i.op_str:
            break
    return out


def roles(listing):
    """Map literal RAM values -> the register they are loaded into (role hint)."""
    out = []
    for a, mn, ops, lit in listing:
        if lit is not None and 0x20000000 <= lit < 0x20050000:
            reg = ops.split(',')[0].strip()
            out.append((a, reg, lit))
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    print("=== persist routine (anchored on header magic 0x%08X) ===" % MAGIC_HDR)
    info = {}
    for path in argv:
        flash, _b, _f = load(path)
        site = magic_sites(flash, MAGIC_HDR)
        print("\n---- %s ----" % path)
        if not site:
            print("   magic ABSENT")
            info[path] = None
            continue
        s = site[0]
        head = prologue_at_or_before(flash, s)
        L = walk(md, flash, head)
        print("   magic @0x%08x  function head 0x%08x  (%d insns)" % (s, head, len(L)))
        print("   RAM globals used, in program order:")
        for a, reg, lit in roles(L):
            print("      0x%08x  -> %s = 0x%08x" % (a, reg, lit))
        info[path] = (head, L)
        # also show non-RAM literals, they identify flash/constants
        consts = [(a, ops.split(',')[0], lit) for a, mn, ops, lit in L
                  if lit is not None and not (0x20000000 <= lit < 0x20050000)]
        print("   other literals:")
        for a, reg, lit in consts:
            print("      0x%08x  -> %s = 0x%08x" % (a, reg, lit))

    print("\n=== role-by-role comparison (layout independent) ===")
    seqs = [(p, roles(L)) for p, v in info.items() if v for L in [v[1]]]
    if len(seqs) == 2 and all(s for _p, s in seqs):
        (p1, s1), (p2, s2) = seqs
        n = min(len(s1), len(s2))
        same = sum(1 for i in range(n) if s1[i][1] == s2[i][1])
        print("  register/role sequence identical at same index: %d / %d" % (same, n))
        print("  %-22s %-22s" % (p1.split('\\')[-1], p2.split('\\')[-1]))
        for i in range(n):
            a1, r1, v1 = s1[i]
            a2, r2, v2 = s2[i]
            flag = "  <-- DIFFERENT ADDRESS" if v1 != v2 else ""
            print("  %-22s %-22s%s" % ("%s=0x%08x" % (r1, v1), "%s=0x%08x" % (r2, v2), flag))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
