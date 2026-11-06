#!/usr/bin/env python3
"""Pick unique 16-byte anchors spread across Application.app for the
file-offset <-> runtime-address mapping (HANDOVER section 6, plan B)."""
import struct, hashlib, os

APP = r"D:\mydata\workspace\data\Application.app"
OUT = r"D:\mydata\workspace\data\app_anchors.txt"
L = 16
d = open(APP, 'rb').read()
N = len(d)
print("file = %s  size = %d (0x%x)" % (APP, N, N))
print("md5  = %s" % hashlib.md5(d).hexdigest())

# index every position -> check uniqueness cheaply by counting occurrences
from collections import defaultdict
occ = defaultdict(int)
step = 1
for i in range(0, N - L + 1):
    occ[d[i:i+L]] += 1

# candidate offsets: a grid, then keep unique windows
cands = []
grid = 0x400  # every 1 KiB
for i in range(0, N - L, grid):
    w = d[i:i+L]
    if occ[w] == 1:
        cands.append(i)
print("unique-window candidates on 0x%x grid: %d" % (grid, len(cands)))

# choose spread: split file into K bands, take the unique candidate closest to
# each band centre, keeping >= 0x8000 apart
K = 24
bands = []
band_sz = N // K
for k in range(K):
    lo, hi = k * band_sz, (k + 1) * band_sz
    centre = (lo + hi) // 2
    pool = [c for c in cands if lo <= c < hi]
    if not pool:
        continue
    best = min(pool, key=lambda c: abs(c - centre))
    if bands and best - bands[-1][0] < 0x4000:
        continue
    bands.append((best, w if False else d[best:best+L]))

# always include the a1.config.write fingerprint from the handover (0x0e9f08, 24 B)
extra = [(0x0e9f08, d[0x0e9f08:0x0e9f08+24])]

with open(OUT, 'w') as f:
    f.write("# anchors: file_offset hex | length | hex bytes   (tab separated)\n")
    f.write("# generated from %s (md5 %s)\n" % (os.path.basename(APP), hashlib.md5(d).hexdigest()))
    for off, w in extra:
        f.write("0x%08x\t%d\t%s\t# handover fingerprint (a1.config.write)\n" % (off, len(w), w.hex()))
    for off, w in bands:
        f.write("0x%08x\t%d\t%s\n" % (off, len(w), w.hex()))
print("wrote %d anchors -> %s" % (len(bands) + len(extra), OUT))
for off, w in extra + bands:
    print("  0x%08x  %s" % (off, w[:16].hex()))
