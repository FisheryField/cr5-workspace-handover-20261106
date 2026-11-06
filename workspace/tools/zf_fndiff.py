"""zf_fndiff.py - compare two Ghidra *listings* (raw instructions) after
normalizing register allocation and absolute addresses.

This is the byte-level counterpart to zf_cdiff.py: it shows exactly which
instructions exist in one build and not the other.

usage: python tools/zf_fndiff.py <a.txt> <b.txt> [--from 0x...] [--to 0x...]
"""
import re, sys, difflib


def load(path, lo=None, hi=None):
    out = []
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'^\s+([0-9a-f]{8})\s+(\S+)\s*(.*)$', line.rstrip())
        if not m:
            continue
        a = int(m.group(1), 16)
        if lo is not None and a < lo:
            continue
        if hi is not None and a > hi:
            continue
        out.append((a, m.group(2), m.group(3).strip()))
    return out


def norm(mn, ops):
    ops = re.sub(r'\b(?:r|s|d|q|sl|sb|fp|ip|lr|pc)\d{1,2}\b', 'REG', ops)
    ops = re.sub(r'\b(?:R|S|D|Q)\d{1,2}\b', 'REG', ops)
    ops = re.sub(r'0x0?80[0-9a-f]{5}', 'ADDR', ops)
    ops = re.sub(r'(?<=[,\s])0x[0-9a-f]{4,8}(?=\b)', 'IMM', ops)
    ops = re.sub(r'\s+', ' ', ops)
    return mn + ' ' + ops


def main():
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    print('A instructions=%d   B instructions=%d' % (len(a), len(b)))
    A = ['%s' % norm(m, o) for _x, m, o in a]
    B = ['%s' % norm(m, o) for _x, m, o in b]
    sa, sb = set(A), set(B)
    print('A mnemonics absent from B:')
    for x in sorted(sa - sb):
        print('   A: %s' % x)
    print('B mnemonics absent from A:')
    for x in sorted(sb - sa):
        print('   B: %s' % x)
    print()
    print('=== aligned diff ===')
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    for tagid, i1, i2, j1, j2 in sm.get_opcodes():
        if tagid == 'equal':
            continue
        print('  [%s] A[%d:%d] B[%d:%d]' % (tagid, i1, i2, j1, j2))
        for k in range(i1, i2):
            print('      A %08x  %s' % (a[k][0], A[k]))
        for k in range(j1, j2):
            print('      B %08x  %s' % (b[k][0], B[k]))


if __name__ == '__main__':
    main()
