"""zf_capdiff.py - instruction-level diff of two address ranges using capstone
for BOTH sides (immune to Ghidra function-boundary artefacts).

usage: python tools/zf_capdiff.py <a_start> <a_len> <b_start> <b_len>
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import load_pair


def norm(mn, ops):
    ops = re.sub(r'\b(?:r|s|d|q|sl|sb|fp|ip|lr|pc)\d{1,2}\b', 'REG', ops)
    ops = re.sub(r'\b(?:R|S|D|Q)\d{1,2}\b', 'REG', ops)
    ops = re.sub(r'0x0?80[0-9a-f]{5}', 'ADDR', ops)
    ops = re.sub(r'\b0x[0-9a-f]{4,8}\b', 'IMM', ops)
    return mn + ' ' + re.sub(r'\s+', ' ', ops).strip()


def main():
    a = int(sys.argv[1], 16)
    al = int(sys.argv[2], 16)
    b = int(sys.argv[3], 16)
    bl = int(sys.argv[4], 16)
    ia, ib = load_pair()
    A = [(i.address, i.mnemonic, i.op_str) for i in ia.dis(a, al)]
    B = [(i.address, i.mnemonic, i.op_str) for i in ib.dis(b, bl)]
    A2 = [(x, norm(m, o)) for x, m, o in A]
    B2 = [(x, norm(m, o)) for x, m, o in B]
    import difflib
    sa = [t for _x, t in A2]
    sb = [t for _x, t in B2]
    print('A(%s) %d insns   B(%s) %d insns' % (ia.name, len(A), ib.name, len(B)))
    sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        print('  [%s] A[%d:%d] B[%d:%d]' % (tag, i1, i2, j1, j2))
        for k in range(i1, i2):
            print('      A %08x  %-9s %s' % (A[k][0], A[k][1], A[k][2]))
        for k in range(j1, j2):
            print('      B %08x  %-9s %s' % (B[k][0], B[k][1], B[k][2]))


if __name__ == '__main__':
    main()
