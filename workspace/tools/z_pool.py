#!/usr/bin/env python3
"""z_pool.py -- read the literal-pool dword a `ldr rX,[pc,#n]` points at, in the
REAL flash address space of the raw .bin (no Ghidra involvement).

usage: python tools\\z_pool.py <tag> 0x08025610 0x08025618 ...
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw


def main(argv):
    tag = argv[0]
    f = Fw(tag)
    for s in argv[1:]:
        a = int(s, 0)
        print('  %08x = %08x' % (a, f.rd32(a)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
