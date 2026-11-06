#!/usr/bin/env python3
"""Query the capstone-derived call map (algs_calls.json).

usage: algs_callers.py <hexaddr> [...]   # who calls these addresses
       algs_callers.py 0x198698 --dis    # disassemble around a site
"""
import bisect
import json
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
CALLS = json.load(open(r"D:\mydata\workspace\tools\algs_calls.json"))


def main():
    addrs = [int(a, 16) for a in sys.argv[1:] if not a.startswith("--")]
    for want in addrs:
        hits = [c for c in CALLS if c[1] == want]
        seen = []
        for ca, _t, cst, cnm in hits:
            if (cst, cnm) not in seen:
                seen.append((cst, cnm))
        print("target 0x%08x : %d call site(s) in %d function(s)"
              % (want, len(hits), len(seen)))
        for ca, _t, cst, cnm in hits:
            print("    site 0x%08x   in %s @0x%08x" % (ca, cnm, cst))
        for cst, cnm in seen:
            print("    -> enclosing symbol %s @0x%08x" % (cnm, cst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
