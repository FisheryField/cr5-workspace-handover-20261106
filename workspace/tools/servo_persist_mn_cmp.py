"""servo_persist_mn_cmp.py - compare the persist routine of the two servo images with
branch targets NORMALISED, so only real differences remain.

Background: an earlier comparison (tools/servo_persist_roles.py) reported
"100/126 identical, 26 differences all branch targets => pure relocation" and stopped
there.  That reasoning was PLAUSIBLE BUT UNVERIFIED - a changed branch target can also
mean changed control flow, and a changed *literal* means changed data.  This script
removes the hand-wave by normalising each category separately:

  * `b`/`bl`/`blx`/`cbz`/`cbnz`/`blt`/... targets -> replaced by a token, because they
    legitimately move between builds
  * PC-relative literal line numbers -> the literal's VALUE is resolved and compared
    instead (a changed constant is a real difference and must not be normalised away)

Then it reports the residue.  Any remaining difference is a genuine behavioural delta.

usage:
  python tools\\servo_persist_mn_cmp.py <a.bin> <b.bin>
"""
import sys, struct, re

FLASH_BASE = 0x08000000
ROUTINES = [
    ('persist', 0x080016de, 0x0800171e),
    ('log_append', 0x080017d0, 0x08001810),
]


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


BRANCH_MN = {'b', 'bl', 'blx', 'bx', 'cbz', 'cbnz', 'beq', 'bne', 'bgt', 'blt',
             'bge', 'ble', 'bhi', 'bls', 'bhs', 'blo', 'bcs', 'bcc', 'bmi', 'bpl'}


def normalise(md, flash, head, mx):
    """Return list of (mnemonic, operand-shape, literal-value-or-None)."""
    out = []
    for i in md.disasm(flash[head - FLASH_BASE:head - FLASH_BASE + mx], head):
        mn, ops = i.mnemonic, i.op_str
        lit = None
        if mn == 'ldr' and 'pc' in ops:
            try:
                off = int(ops.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                    lit = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
            except ValueError:
                pass
        if mn in BRANCH_MN:
            ops = re.sub(r'#0x[0-9a-f]+', '#TGT', ops)
        elif mn == 'ldr' and 'pc' in ops:
            ops = re.sub(r'\[pc, #0x[0-9a-f]+\]', '[pc]', ops)
        else:
            ops = re.sub(r'#0x[0-9a-f]+', lambda m: m.group(0), ops)
        out.append((i.address, mn, ops, lit))
        if mn.startswith('pop') and 'pc' in ops:
            break
        if mn == 'bx' and 'lr' in ops:
            break
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    A = load(argv[0])[2]
    B = load(argv[1])[2]
    print("A %s\nB %s" % (argv[0], argv[1]))

    for name, ha, hb in ROUTINES:
        print("\n" + "=" * 70)
        print("=== %s : 0x%08x vs 0x%08x ===" % (name, ha, hb))
        la = normalise(md, A, ha, 0x200)
        lb = normalise(md, B, hb, 0x200)
        print("  insns: %d vs %d" % (len(la), len(lb)))
        n = min(len(la), len(lb))
        same = 0
        diffs = []
        for k in range(n):
            a1, m1, o1, l1 = la[k]
            a2, m2, o2, l2 = lb[k]
            if (m1, o1, l1) == (m2, o2, l2):
                same += 1
            else:
                diffs.append((k, la[k], lb[k]))
        print("  RESIDUE (normalised, incl. literal VALUES): %d identical / %d  (%.1f%%)"
              % (same, n, 100.0 * same / max(1, n)))
        print("  %d residual difference(s):" % len(diffs))
        for k, x, y in diffs:
            l1 = ('lit=0x%08x' % x[3]) if x[3] is not None else ''
            l2 = ('lit=0x%08x' % y[3]) if y[3] is not None else ''
            same_lit = (x[3] == y[3])
            tag = ''
            if x[3] is not None or y[3] is not None:
                tag = '   LITERAL SAME' if same_lit else '   *** LITERAL DIFFERS ***'
            print("    [%3d] A 0x%08x %-9s %-24s %-14s | B 0x%08x %-9s %-24s %s%s"
                  % (k, x[0], x[1], x[2], l1, y[0], y[1], y[2], l2, tag))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
