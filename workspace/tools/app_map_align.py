#!/usr/bin/env python3
"""Align Application.app (file offsets) against a runtime memory dump.

For each of a grid of file windows, report the runtime address of the first
occurrence(s) in the dump, then print (dump_addr - file_off) per hit so that
segments with a constant delta become obvious.

usage: app_map_align.py <dump.bin> <dump_base_hex> [window] [grid]
"""
import sys, struct, hashlib, collections

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
dump_base = int(sys.argv[2], 16)
W = int(sys.argv[3]) if len(sys.argv) > 3 else 24
GRID = int(sys.argv[4]) if len(sys.argv) > 4 else 0x400

f = open(APP, 'rb').read()
m = open(dump_path, 'rb').read()
print("file  %d (0x%x)  md5 %s" % (len(f), len(f), hashlib.md5(f).hexdigest()))
print("dump  %d (0x%x)  base 0x%x" % (len(m), len(m), dump_base))

# index the dump: map window bytes -> list of offsets in dump (fast enough via
# substring search per distinct window; dump is ~2.3 MB and windows ~10k)
hits = []
for off in range(0, len(f) - W + 1, GRID):
    w = f[off:off + W]
    pos = []
    i = m.find(w)
    while i != -1 and len(pos) < 8:
        pos.append(i)
        i = m.find(w, i + 1)
    if pos:
        hits.append((off, pos))

print("checked %d windows of %d bytes, %d had at least one hit" %
      (len(range(0, len(f) - W + 1, GRID)), W, len(hits)))

print()
print("file_off   -> runtime addr(s)                        delta = addr - off")
prev_delta = None
rows = []
for off, pos in hits:
    ds = []
    for p in pos:
        addr = dump_base + p
        ds.append((addr, addr - off))
    row = (off, ds)
    rows.append(row)

for off, ds in rows:
    s = "  ".join("0x%08x(d=%+d)" % (a, d) for a, d in ds[:3])
    print("0x%08x -> %s" % (off, s))

print()
print("=== delta histogram (all hits) ===")
c = collections.Counter()
for off, ds in rows:
    for a, d in ds:
        c[d] += 1
for d, n in c.most_common(20):
    print("  delta %+d (0x%x) x%d" % (d, d & 0xffffffff, n))

# try to fit monotone delta ranges: find the longest run of rows whose first
# hit has constant delta
print()
print("=== monotone delta runs (using the hit closest to the previous addr) ===")
run_start = None
last_delta = None
runs = []
for off, ds in rows:
    d = ds[0][1]
    if d == last_delta:
        continue
    if run_start is not None:
        runs.append((run_start, prev_off, last_delta))
    run_start = off
    last_delta = d
    prev_off = off
    last_delta = d
runs.append((run_start, rows[-1][0], last_delta)) if rows else None
for a, b, d in runs[:40]:
    print("  file 0x%08x..0x%08x  delta 0x%x" % (a, b, d & 0xffffffff))
