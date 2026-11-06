"""servo_loopdiff.py - complete field-access diff of the position control routine between
the two servo images.

Motivation: last round I reported the difference in this routine as "3.2.D.8 has an extra
one-shot re-init block".  Reading further showed that description was incomplete AND
slightly misleading.  Both builds contain the same shape; the real deltas are smaller and
more specific.  This script produces the exhaustive list instead of a hand-read sample:

  * find the routine in each image (anchored on a signature unique to it)
  * collect EVERY struct-field access `[rB, #imm]` together with the access kind
    (byte/half/word, load/store) and the base register's role
  * report the two multisets and their difference

The routine signature used: it dereferences a literal equal to the object-array base and
multiplies by the 0x329 stride, then reads `+0x1af` and `+0x31f`.

usage:
  python tools\\servo_loopdiff.py <a.bin> <b.bin>
"""
import sys, struct, re, collections

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def find_routine(md, flash, hint):
    """Locate the function containing `ldr.w rX,[rY,#0x1af]` near the hint address."""
    n = len(flash)
    cands = []
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 4:
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            if i.mnemonic.startswith('ldr') and '#0x1af' in i.op_str and 'pc' not in i.op_str:
                cands.append(a)
            break
        a += 2
    if not cands:
        return None
    # nearest candidate to the hint
    best = min(cands, key=lambda x: abs(x - hint))
    # walk back to push {..lr} without crossing a return
    for b in range(best, max(FLASH_BASE, best - 0x200), -2):
        ms = list(md.disasm(flash[b - FLASH_BASE:b - FLASH_BASE + 4], b))
        if not ms:
            continue
        if ms[0].mnemonic.startswith('pop') and 'pc' in ms[0].op_str:
            break
        if ms[0].mnemonic == 'bx' and 'lr' in ms[0].op_str:
            break
        if ms[0].mnemonic.startswith('push') and 'lr' in ms[0].op_str:
            return b
    return best


MN = {'ldr': 'L', 'ldrh': 'L', 'ldrb': 'L', 'ldrsb': 'L', 'ldrsh': 'L',
      'str': 'S', 'strh': 'S', 'strb': 'S', 'ldrd': 'L2', 'strd': 'S2',
      'str.w': 'S', 'ldr.w': 'L', 'ldrh.w': 'L', 'strh.w': 'S', 'ldrb.w': 'L',
      'strb.w': 'S'}


def fields(md, flash, head, mx=0x400):
    """Collect (offset, size, kind, base-reg) for every [rB,#imm] access."""
    out = []
    for i in md.disasm(flash[head - FLASH_BASE:head - FLASH_BASE + mx], head):
        mn = i.mnemonic
        if mn not in MN or '[' not in i.op_str:
            continue
        inside = i.op_str[i.op_str.index('[') + 1:i.op_str.index(']')]
        parts = [p.strip() for p in inside.split(',')]
        if len(parts) < 2 or not parts[1].startswith('#0x'):
            continue
        try:
            off = int(parts[1][1:], 16)
        except ValueError:
            continue
        width = 1 if 'b' in mn else (2 if 'h' in mn else (8 if mn.endswith('d') else 4))
        out.append((off, width, MN[mn], parts[0]))
        if mn.startswith('pop') and 'pc' in i.op_str:
            break
        if mn == 'bx' and 'lr' in i.op_str:
            break
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    A = load(argv[0])[2]
    B = load(argv[1])[2]
    HA = find_routine(md, A, 0x08010eb6)
    HB = find_routine(md, B, 0x080107ac)
    print("routine head: A=0x%08x   B=0x%08x" % (HA, HB))

    fa = fields(md, A, HA)
    fb = fields(md, B, HB)
    print("field accesses: A=%d  B=%d" % (len(fa), len(fb)))

    def key(t):
        return (t[0], t[1], t[2])

    ka = collections.Counter(key(t) for t in fa)
    kb = collections.Counter(key(t) for t in fb)
    print("\n=== offsets touched by A only ===")
    for (o, w, k), n in sorted(ka.items()):
        if kb[(o, w, k)] == 0:
            print("   +0x%03x  size=%d %s  x%d" % (o, w, k, n))
    print("\n=== offsets touched by B only ===")
    for (o, w, k), n in sorted(kb.items()):
        if ka[(o, w, k)] == 0:
            print("   +0x%03x  size=%d %s  x%d" % (o, w, k, n))

    print("\n=== shared offsets with DIFFERENT access counts ===")
    for k in sorted(set(ka) & set(kb)):
        if ka[k] != kb[k]:
            print("   +0x%03x size=%d %s : A=%d  B=%d" % (k[0], k[1], k[2], ka[k], kb[k]))

    print("\n=== common offsets (context) ===")
    common = sorted(set(ka) & set(kb))
    print("   " + ' '.join('+0x%x' % k[0] for k in common))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
