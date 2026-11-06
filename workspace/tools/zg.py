#!/usr/bin/env python3
"""zg.py -- run several z_gh.java commands in ONE Ghidra session, write the full
output to .zwork/gh.log, and print it.

Addresses given here are TRUE flash addresses (0x08010000+); they are shifted
down by 0x10000 for the Ghidra project and shifted back in the output.

usage:
  python tools\\zg.py b decomp 0x08022390 dis 0x08022390 40
  python tools\\zg.py a decomp 0x08022596
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zgh  # reuse paths + lock retry

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.zwork')


def main(argv):
    which = argv[0]
    cmds = argv[1:]
    # zgh.run already shifts addresses and retags output
    txt, raw = zgh.run(which, cmds)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'gh.log'), 'w', encoding='utf-8') as f:
        f.write(txt)
        f.write('\n\n=== RAW TAIL ===\n')
        f.write(raw[-4000:])
    print(txt)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
