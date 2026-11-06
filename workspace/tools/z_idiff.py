#!/usr/bin/env python3
"""z_idiff.py -- normalised instruction diff between two functions in the two
servo images.

Normalisation makes the diff report SEMANTIC differences rather than
re-linking noise:
  * a `ldr rX,[pc,#n]` is replaced by the VALUE it loads, and that value is
    mapped to a symbolic class:
        RAM:<addr>        a RAM global (addresses differ between builds)
        FLASH:<addr>      a flash constant
        NUM:<value>       a plain number
  * branch targets are dropped (they move with code layout)
  * registers are kept, because the position chain's dataflow depends on them

usage:
  python tools\\z_idiff.py <tagA> <startA> <endA> <tagB> <startB> <endB>
"""
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw


def normalise(f, start, end):
    out = []
    for i in f.dis(start, 800):
        if i.address > end:
            break
        mn = i.mnemonic
        ops = i.op_str
        lit = None
        if 'pc' in ops and '#' in ops and '[' in ops:
            try:
                imm = int(ops.split('#')[-1].rstrip(']'), 0)
                t = ((i.address + 4) & ~3) + imm
                if f.base <= t <= f.end - 4:
                    v = f.rd32(t)
                    if 0x20000000 <= v < 0x20060000:
                        lit = 'RAM'
                    elif 0x08000000 <= v < 0x08100000:
                        lit = 'FLASH'
                    else:
                        lit = 'NUM:%d' % v
            except ValueError:
                pass
        if lit:
            ops = re.sub(r'\[pc,[^\]]*\]', lit, ops)
        # drop branch targets
        if mn.startswith('b') or mn in ('cbz', 'cbnz'):
            ops = re.sub(r'#0x[0-9a-f]+', '#T', ops)
        out.append((i.address, i.bytes.hex(), mn, ops))
    return out


def shape(mn, ops):
    """operand shape: registers -> r, immediates -> #, memory -> [..]"""
    s = re.sub(r'\br1[0-2]\b|\br[0-9]\b|\bsb\b|\bsl\b|\bfp\b|\bip\b|\bsp\b|\blr\b|\bpc\b', 'r', ops)
    s = re.sub(r'#-?0x[0-9a-f]+', '#', s)
    s = re.sub(r'#-?\d+', '#', s)
    return '%s %s' % (mn, s)


def main(argv):
    tagA, a0, a1, tagB, b0, b1 = argv[0], int(argv[1], 0), int(argv[2], 0), argv[3], int(argv[4], 0), int(argv[5], 0)
    fa, fb = Fw(tagA), Fw(tagB)
    A = normalise(fa, a0, a1)
    B = normalise(fb, b0, b1)
    print('== %s 0x%08x..0x%08x : %d insns   vs   %s 0x%08x..0x%08x : %d insns'
          % (tagA, a0, a1, len(A), tagB, b0, b1, len(B)))
    sa = [shape(m, o) for _a, _by, m, o in A]
    sb = [shape(m, o) for _a, _by, m, o in B]
    sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
    opcodes = sm.get_opcodes()
    nnum = 0
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            # still report pairs whose literal VALUE differs (RAM vs RAM)
            for k in range(i2 - i1):
                va = A[i1 + k][3]
                vb = B[j1 + k][3]
                if va != vb:
                    print('  ~LIT  A[%s] %-9s %-30s   B[%s] %-9s %-30s'
                          % ('%08x' % A[i1 + k][0], A[i1 + k][2], va,
                             '%08x' % B[j1 + k][0], B[j1 + k][2], vb))
                    nnum += 1
            continue
        print('  %s  A[%d..%d) B[%d..%d)' % (tag.upper(), i1, i2, j1, j2))
        for k in range(i1, i2):
            print('     -  %08x  %-14s %-9s %s' % (A[k][0], A[k][1], A[k][2], A[k][3]))
        for k in range(j1, j2):
            print('     +  %08x  %-14s %-9s %s' % (B[k][0], B[k][1], B[k][2], B[k][3]))
        nnum += 1
    print('== change blocks: %d   literal-value-only diffs: %d' % (len(opcodes), nnum))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
