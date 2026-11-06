#!/usr/bin/env python3
"""Verify a single candidate (file_off -> runtime_addr) mapping hypothesis and
show exactly where and how the two streams diverge.

usage: app_map_verify.py <dump.bin> <dump_base_hex> <file_off_hex> <run_hex>
"""
import sys

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
fo = int(sys.argv[3], 16)
run = int(sys.argv[4], 16)
f = open(APP, 'rb').read()
m = open(dump_path, 'rb').read()

# delta implied by the seed
seed_f, seed_a = 0x400, 0x75a960d0
delta = seed_a - seed_f
print("seed delta = 0x%x  => file 0x%x maps to 0x%x" % (delta, fo, fo + delta))

print()
print("=== trivial check: compare the two regions directly ===")
bad = 0
first_bad = None
i = 0
while i < run:
    a = fo + i
    b = fo + delta + i - base
    if b < 0 or b >= len(m):
        print("  run past end of dump at i=0x%x" % i)
        break
    if f[a] != m[b]:
        if first_bad is None:
            first_bad = i
        bad += 1
        if bad <= 12:
            print("  DIFF at file 0x%08x / mem 0x%08x" % (a, fo + delta + i))
            lo = i - 16
            if lo < 0:
                lo = 0
            print("    file: %s" % f[fo + lo:fo + i + 16].hex(' '))
            print("    mem : %s" % m[fo + delta + lo - base:fo + delta + i + 16 - base].hex(' '))
    i += 1
print("  compared 0x%x bytes, %d differ (first at +0x%x)" %
      (i, bad, first_bad if first_bad is not None else -1))
