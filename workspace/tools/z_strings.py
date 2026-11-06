#!/usr/bin/env python3
"""z_strings.py -- strict string extractor for the two servo images.

Filter (validated by positive controls 'TxPDO assign' and 'Position Actual Value'):
  chars in [A-Za-z0-9 ._/-], length >= 8, letters >= 60%, lowercase >= half the
  letters, no double space.
Prints "file_offset  flash_addr  string" for every hit (and optionally greps).
"""
import os
import re
import sys

ALLOW = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ._/-')
BASE = 0x08010000
IMGS = {
    '3150': r'data/servo_fw_samples/elf/v3150.bin',
    'd8': r'data/servo_fw_samples/elf/v328d8.bin',
}


def good_strings(d, mn=8):
    out = []
    i, n = 0, len(d)
    while i < n:
        j = i
        while j < n and d[j] in ALLOW:
            j += 1
        if j - i >= mn:
            s = d[i:j]
            al = sum(1 for c in s if 65 <= c <= 90 or 97 <= c <= 122)
            lo = sum(1 for c in s if 97 <= c <= 122)
            if al >= mn * 0.6 and lo * 2 >= al and b'  ' not in s:
                out.append((i, s))
        i = max(j, i + 1)
    return out


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # tags are the tokens '3150' / 'd8'; everything else is a regex filter
    tags = [a for a in argv if a in IMGS] or list(IMGS)
    pats = [a for a in argv if a not in IMGS]
    for tag in tags:
        d = open(os.path.join(root, IMGS[tag]), 'rb').read()
        g = good_strings(d)
        print('== %s : %d strings' % (tag, len(g)))
        for a, s in g:
            txt = s.decode('latin1')
            if pats and not any(re.search(p, txt, re.I) for p in pats):
                continue
            print('   %06x  0x%08x  %s' % (a, BASE + a, txt))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
