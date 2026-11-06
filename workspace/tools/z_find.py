#!/usr/bin/env python3
"""z_find.py -- locate the code that materialises a *data pointer* in the two
servo images, with mandatory positive controls.

Why
---
Three separate searches in this session returned 0 for things that exist.  Every
run here first resolves a control pointer that is known (from a decompiled
Ghidra listing) to be loaded with `ldr rX,[pc,#n]`, and refuses to report if the
control fails.

usage:
  python tools\\z_find.py <tag> ctrl <addr>+   -- verify literal-pool resolution
  python tools\\z_find.py <tag> pool <hexdword> [more...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw


def main(argv):
    tag = argv[0]
    mode = argv[1]
    f = Fw(tag)
    if mode == 'ctrl':
        print('== control: resolve each address as a literal-pool dword')
        for s in argv[2:]:
            a = int(s, 0)
            print('  %08x = %08x' % (a, f.rd32(a)))
        return 0
    if mode == 'pool':
        for s in argv[2:]:
            v = int(s, 0)
            pat = struct.pack('<I', v)
            hits = []
            o = f.code.find(pat)
            while o >= 0:
                hits.append(f.base + o)
                o = f.code.find(pat, o + 1)
            print('  %08x (%d) -> %d hit(s) %s' % (v, v, len(hits),
                  ' '.join('%08x' % h for h in hits[:20])))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
