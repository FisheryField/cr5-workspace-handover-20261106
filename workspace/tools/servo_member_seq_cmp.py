"""servo_member_seq_cmp.py - align the two servo images by the SEQUENCE of object-member
offsets and diff the corresponding code.

Idea: the OD access code walks objects in a fixed program order, emitting
`movw rX,#0x329 ; ... ; add rX,#FIELD`.  That sequence of FIELD values is a layout
fingerprint: it is the same logical program in both builds even though addresses move.
So it can be used as an alignment key:

  1. extract [site address, member offset] for each image, in address order
  2. align the two offset sequences (difflib on the offset lists) -> pairs of
     corresponding sites
  3. for each aligned pair, compare the instruction shape of a fixed window around the
     site (mnemonic + operand text with absolute branch targets and RAM addresses
     normalised), and report windows that differ

This is the method that can actually find "what did 3.2.D.8 change" in this layer,
because it is immune to layout shifts.

usage:
  python tools\\servo_member_seq_cmp.py <a.bin> <b.bin> [--max-report 30]
"""
import sys, struct, re, difflib

FLASH_BASE = 0x08000000
STRIDE = 0x329
WIN = 0x20


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def extract(md, flash):
    out = []
    a = FLASH_BASE
    n = len(flash)
    while a <= FLASH_BASE + n - 8:
        ms = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if ms and ms[0].mnemonic == 'movw' and ms[0].op_str.split(', ')[-1] == '#0x329':
            off = None
            for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 0x40], a):
                if i.address == a:
                    continue
                if i.mnemonic.startswith('add') and '#' in i.op_str:
                    try:
                        v = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                    except ValueError:
                        continue
                    if v and v != STRIDE:
                        off = v
                        break
            out.append((a, off))
        a += 2
    return out


def norm_shape(md, flash, site):
    """Instruction shape of a window, with absolute targets/addresses normalised."""
    shp = []
    for i in md.disasm(flash[site - FLASH_BASE:site - FLASH_BASE + WIN], site):
        ops = i.op_str
        ops = re.sub(r'#0x[0-9a-f]+', '#IMM', ops)
        ops = re.sub(r'\[pc, #IMM\]', '[pc]', ops)
        shp.append((i.mnemonic, ops))
    return shp


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    maxrep = int(argv[argv.index('--max-report') + 1]) if '--max-report' in argv else 30

    A = extract(md, load(argv[0])[2])
    B = extract(md, load(argv[1])[2])
    fa = load(argv[0])[2]
    fb = load(argv[1])[2]
    print("A %s : %d sites" % (argv[0], len(A)))
    print("B %s : %d sites" % (argv[1], len(B)))

    sa = [o if o is not None else -1 for _a, o in A]
    sb = [o if o is not None else -1 for _a, o in B]
    sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
    ops = sm.get_opcodes()
    # NOTE: count matched elements, not opcode blocks.  An earlier version of this
    # script summed `b - a` over opcodes and printed 0%, which contradicted the
    # per-block listing directly beneath it.
    eq = 0
    for tag, a, b, _c, _d in ops:
        if tag == 'equal':
            eq += (b - a)
    print("\n=== offset-sequence alignment ===")
    print("  matched sites: %d / %d (A)  %.1f%%" % (eq, len(sa), 100.0 * eq / max(1, len(sa))))
    print("  (B has %d sites; the surplus shows up as insert/replace blocks below)" % len(sb))
    for tag, i1, i2, j1, j2 in ops:
        if tag != 'equal':
            print("  %-8s A[%d:%d] len %d  vs  B[%d:%d] len %d  offsA=%s offsB=%s" %
                  (tag, i1, i2, i2 - i1, j1, j2, j2 - j1,
                   [hex(x) for x in sa[i1:i2][:8]], [hex(x) for x in sb[j1:j2][:8]]))

    print("\n=== aligned-window shape differences (first %d) ===" % maxrep)
    shown = 0
    for tag, i1, i2, j1, j2 in ops:
        if tag != 'equal':
            continue
        for k in range(i2 - i1):
            aa = A[i1 + k][0]
            bb = B[j1 + k][0]
            ha = norm_shape(md, fa, aa)
            hb = norm_shape(md, fb, bb)
            n = min(len(ha), len(hb))
            same = sum(1 for i in range(n) if ha[i] == hb[i])
            if n and same / n < 0.75:
                print("  A 0x%08x (+0x%x) vs B 0x%08x (+0x%x) : shape match %d/%d" %
                      (aa, A[i1 + k][1] or 0, bb, B[j1 + k][1] or 0, same, n))
                shown += 1
                if shown >= maxrep:
                    return 0
    print("  %d window(s) with <75%% shape match" % shown)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
