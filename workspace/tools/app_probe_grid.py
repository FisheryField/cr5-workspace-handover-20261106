#!/usr/bin/env python3
"""Fast pass 1: which file regions of Application.app are present verbatim in a
process memory dump, and how they are laid out.

Uses one linear sweep of the dump to build a set of 32-byte windows at
4-byte-aligned positions, then tests the file on the same grid.  Because the
loader keeps 4-byte alignment, presence on the file grid is a reliable signal.

usage: app_probe_grid.py <dump[.gz]> <dump_base_hex>
"""
import sys, gzip, hashlib, collections

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
W = 32
GRID = 4

f = open(APP, 'rb').read()
m = gzip.open(dump_path, 'rb').read() if dump_path.endswith('.gz') else open(dump_path, 'rb').read()
FN, MN = len(f), len(m)
print("file 0x%08x  dump 0x%08x  base 0x%08x" % (FN, MN, base))

# --- index the dump: distinct 32-byte window -> first offsets (aligned) ---
idx = {}
for i in range(0, MN - W, GRID):
    w = m[i:i + W]
    if w in idx:
        v = idx[w]
        if v is not None:
            if len(v) < 4:
                v.append(i)
            else:
                idx[w] = None       # too common, useless as an anchor
    else:
        idx[w] = [i]
print("dump windows indexed: %d distinct" % len(idx))
uniq = {w: v[0] for w, v in idx.items() if v is not None and len(v) == 1}
print("unique dump windows:  %d" % len(uniq))
del idx

# --- sweep the file ---
present = bytearray((FN // GRID) + 1)
anchor = {}
for k, fo in enumerate(range(0, FN - W, GRID)):
    w = f[fo:fo + W]
    i = uniq.get(w)
    if i is not None:
        present[k] = 1
        anchor[fo] = i

print("file windows on grid: %d, present in dump: %d" % (FN // GRID, len(anchor)))

# --- contiguous runs of present windows ---
runs = []
cur = None
for k in range(len(present)):
    if present[k]:
        if cur is None:
            cur = [k, k]
        else:
            cur[1] = k
    else:
        if cur is not None:
            runs.append(cur)
            cur = None
if cur:
    runs.append(cur)

print()
print("=== %d present runs ===" % len(runs))
tot = 0
for a, b in runs:
    fa, fb = a * GRID, (b * GRID) + W
    tot += fb - fa
    # runtime location(s) of this run
    locs = collections.Counter()
    for fo in range(fa, fb, max(GRID, (fb - fa) // 8 or GRID)):
        i = anchor.get(fo)
        if i is not None:
            locs[base + i - fo] += 1
    s = ", ".join("0x%08x x%d" % (d, n) for d, n in locs.most_common(4))
    print("  file 0x%08x-0x%08x (%8d B)  delta: %s" % (fa, fb, fb - fa, s))
print("total present: %d / %d (%.2f%%)" % (tot, FN, 100.0 * tot / FN))
