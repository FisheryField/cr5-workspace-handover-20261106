"""servo_func_at.py - find the enclosing function of an address and dump it.

Used to resolve difference (1) between the two servo images: at one logical slot the
object-array math differs between builds:

    v3.2.D.8  0x08016A6E  movw sl,#0x115 ; mul sl,r4,sl        (stride 277)
    v3.1.5.0  0x080164D0  add.w r0,r7,r7,lsl#2 ; add.w r0,r0,r7,lsl#6   (x69)

Reading only a 0x20-byte window is not enough to say what that index means, so this
finds the function boundaries and prints the whole thing.

Boundary heuristics (ARM/Thumb, no symbols):
  * head: nearest `push {...,lr}` at or before the address, reached without crossing
    an unconditional `pop {...,pc}` / `bx lr`
  * tail: the matching `pop {...,pc}`

usage:
  python tools\\servo_func_at.py <flash.bin> --at 0x08016a3a [--max 0x400]
  python tools\\servo_func_at.py <flash.bin> --at 0x08016a3a --compare <other.bin> --at2 0x0801649c
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


def find_head(md, flash, addr, limit=0x600):
    """Nearest push {...,lr} at or before addr, not crossing a return."""
    best = None
    for a in range(addr, max(FLASH_BASE, addr - limit), -2):
        ms = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if not ms:
            continue
        i = ms[0]
        if i.mnemonic.startswith('pop') and 'pc' in i.op_str:
            break
        if i.mnemonic == 'bx' and 'lr' in i.op_str:
            break
        if i.mnemonic.startswith('push') and 'lr' in i.op_str:
            best = a
            break
    return best


def dump(md, flash, head, mx):
    out = []
    for i in md.disasm(flash[head - FLASH_BASE:head - FLASH_BASE + mx], head):
        lit = ''
        if i.mnemonic == 'ldr' and 'pc' in i.op_str:
            try:
                off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                    v = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                    lit = '   ; lit = 0x%08x' % v
            except ValueError:
                pass
        if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
            lit += '   -> 0x%08x' % (int(i.op_str[1:], 0) & ~1)
        out.append((i.address, i.mnemonic, i.op_str, lit))
        if i.mnemonic.startswith('pop') and 'pc' in i.op_str:
            break
        if i.mnemonic == 'bx' and 'lr' in i.op_str:
            break
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    flash = load(path)[2]
    at = int(argv[argv.index('--at') + 1], 16)
    mx = int(argv[argv.index('--max') + 1], 16) if '--max' in argv else 0x400

    head = find_head(md, flash, at)
    print("### %s" % path)
    print("  probe 0x%08x -> function head %s" % (at, ('0x%08x' % head) if head else '?'))
    if not head:
        return 1
    L = dump(md, flash, head, mx)
    print("  %d instructions, span 0x%08x..0x%08x (%d B)" %
          (len(L), head, L[-1][0], L[-1][0] + 4 - head))
    for a, mn, ops, lit in L:
        mark = '  <<< probed' if a == at else ''
        print("  %08x: %-9s %-30s%s%s" % (a, mn, ops, lit, mark))

    if '--compare' in argv:
        other = argv[argv.index('--compare') + 1]
        at2 = int(argv[argv.index('--at2') + 1], 16)
        f2 = load(other)[2]
        h2 = find_head(md, f2, at2)
        print("\n### %s" % other)
        print("  probe 0x%08x -> function head %s" % (at2, ('0x%08x' % h2) if h2 else '?'))
        if h2:
            L2 = dump(md, f2, h2, mx)
            print("  %d instructions, span 0x%08x..0x%08x (%d B)" %
                  (len(L2), h2, L2[-1][0], L2[-1][0] + 4 - h2))
            for a, mn, ops, lit in L2:
                mark = '  <<< probed' if a == at2 else ''
                print("  %08x: %-9s %-30s%s%s" % (a, mn, ops, lit, mark))

            print("\n### shape comparison (normalised) ###")
            import re
            def shp(L):
                o = []
                for _a, mn, ops, _l in L:
                    s = re.sub(r'#0x[0-9a-f]+', '#IMM', ops)
                    o.append((mn, s))
                return o
            s1, s2 = shp(L), shp(L2)
            n = min(len(s1), len(s2))
            same = sum(1 for i in range(n) if s1[i] == s2[i])
            print("  %d vs %d insns; identical (normalised) at same index: %d/%d = %.1f%%" %
                  (len(s1), len(s2), same, n, 100.0 * same / max(1, n)))
            shown = 0
            for i in range(n):
                if s1[i] != s2[i]:
                    print("    [%3d] A %-9s %-26s | B %-9s %s" %
                          (i, s1[i][0], s1[i][1], s2[i][0], s2[i][1]))
                    shown += 1
                    if shown >= 25:
                        print("    ...")
                        break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
