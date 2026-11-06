#!/usr/bin/env python3
"""z_dis.py -- capstone disassembler for the two servo images, reporting the
REAL flash address (0x08010000 + file offset).

Relative to the Ghidra projects (which were imported from an ELF whose .text
section is labelled 0x08000000), the addresses printed here are +0x10000.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    tag = argv[0]
    a = int(argv[1], 0)
    n = int(argv[2]) if len(argv) > 2 else 30
    bias = 0
    if '--bias' in argv:
        bias = int(argv[argv.index('--bias') + 1], 0)
    f = Fw(tag)
    start = a + bias
    print('== %s  real 0x%08x  (%d insns)' % (tag, start, n))
    # show a little context before
    for i in f.dis(start, n):
        print('  %08x  %-14s %s' % (i.address, i.bytes.hex(), i.mnemonic + ' ' + i.op_str))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
