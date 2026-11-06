#!/usr/bin/env python3
"""z_fbounds.py -- find the enclosing function start for an address by scanning
backwards for a Thumb function prologue (push/push.w ... lr ...), and print the
function body plus a normalised instruction diff against another address in the
other image.

usage:
  python tools\\z_fbounds.py d8 0x08025602
  python tools\\z_idiff.py ...
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw

PROLOGUE = ('push', 'push.w', 'stmdb', 'vpush')


def find_start(f, addr, back=0x1000):
    lo = max(f.base, addr - back)
    # disassemble the window from several alignments, keep prologue candidates
    cands = []
    for start in range(lo, addr, 2):
        ins = list(f.dis(start, 1))
        if not ins:
            continue
        i = ins[0]
        if i.mnemonic in PROLOGUE and 'lr' in i.op_str:
            cands.append(start)
    # the innermost prologue that still reaches addr
    return cands[-1] if cands else None


def body(f, start, maxn=400):
    out = []
    for i in f.dis(start, maxn):
        out.append(i)
        if i.mnemonic in ('pop', 'pop.w') and 'pc' in i.op_str:
            break
        if i.mnemonic in ('bx', 'b') and i.op_str.strip() == 'lr':
            break
    return out


def main(argv):
    tag = argv[0]
    addr = int(argv[1], 0)
    f = Fw(tag)
    s = find_start(f, addr)
    print('== %s enclosing function start for 0x%08x : %s'
          % (tag, addr, hex(s) if s else 'NOT FOUND'))
    if s is None:
        return 1
    b = body(f, s)
    print('   body: %d instructions, %d bytes' % (len(b), sum(i.size for i in b)))
    for i in b:
        print('   0x%08x  %-14s %s' % (i.address, i.bytes.hex(), i.mnemonic + ' ' + i.op_str))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
