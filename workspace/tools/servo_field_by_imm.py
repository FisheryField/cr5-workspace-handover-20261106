"""servo_field_by_imm.py - enumerate every instruction touching `[rX, #IMM]` regardless of
how rX was computed, and compare two images.

Why: tools/servo_field_refs.py needs to prove the base register's value, so it misses
bases like `base + axis*0x329` (documented gap, §18.6).  For a field like the per-axis
state word at +0x20 (used by the 3.1.5.0 state machine that 3.2.D.8 lacks) that gap
hides exactly the accesses we care about.

This is the brute-force counterpart: list every load/store whose displacement equals the
requested immediate, with the instruction, and diff the two images' site lists.  It
cannot tell you WHICH struct an access belongs to - that is the trade-off - but it
cannot miss an access either, which makes it the right tool for a *census*.

usage:
  python tools\\servo_field_by_imm.py <a.bin> <b.bin> --imm 0x24 [--only R|W] [--base r1]
"""
import sys, struct
from collections import Counter

FLASH_BASE = 0x08000000
LD = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd')
ST = ('str', 'strh', 'strb', 'strd')


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def norm(mn):
    return mn[:-2] if mn.endswith('.w') else mn


def census(md, flash, IMM, only=None, base_filter=None):
    out = []
    a = FLASH_BASE
    n = len(flash)
    while a <= FLASH_BASE + n - 4:
        ins = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if not ins:
            a += 2
            continue
        i = ins[0]
        mn = norm(i.mnemonic)
        if mn in LD + ST and '[' in i.op_str and '#0x%x]' % IMM in i.op_str.replace(' ', ''):
            body = i.op_str[i.op_str.index('[') + 1:].split(']')[0]
            parts = [x.strip() for x in body.split(',')]
            base = parts[0]
            if base_filter and base != base_filter:
                a += i.size
                continue
            kind = 'W' if mn in ST else 'R'
            if only and kind != only:
                a += i.size
                continue
            out.append((i.address, i.mnemonic, i.op_str, base, kind))
        a += i.size
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    IMM = int(argv[argv.index('--imm') + 1], 16)
    only = argv[argv.index('--only') + 1].upper() if '--only' in argv else None
    bf = argv[argv.index('--base') + 1] if '--base' in argv else None

    imgs = [p for p in argv if p.endswith('.bin')]
    if len(imgs) != 2:
        raise SystemExit("need exactly two .bin paths")
    res = {}
    for p in imgs:
        flash = load(p)[2]
        res[p] = census(md, flash, IMM, only, bf)

    for p in imgs:
        rows = res[p]
        print("### %s   [rX, #0x%X] %s  -> %d site(s)" %
              (p, IMM, ('kind=' + only) if only else '', len(rows)))
        c = Counter(r[3] for r in rows)
        print("    base-register histogram: %s" % dict(c))
        for a, mn, ops, base, kind in rows:
            print("    0x%08x  %-9s %-26s base=%-4s %s" % (a, mn, ops, base, kind))
        print()

    if len(imgs) == 2:
        ka = Counter((r[1], r[3], r[4]) for r in res[imgs[0]])
        kb = Counter((r[1], r[3], r[4]) for r in res[imgs[1]])
        print("=== shape comparison (mnemonic, base, kind) ===")
        print("  %-28s %6s %6s" % ("shape", "A", "B"))
        for k in sorted(set(ka) | set(kb)):
            print("  %-28s %6d %6d  %s" %
                  ('%s [%s] %s' % k, ka.get(k, 0), kb.get(k, 0),
                   '' if ka.get(k, 0) == kb.get(k, 0) else '<-- DIFFERS'))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
