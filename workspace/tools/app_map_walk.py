#!/usr/bin/env python3
"""Exact file-offset <-> runtime-address map for Application.app.

Walks the file and the runtime dump together:
  * inside a segment the two advance in lockstep (mapping = addr - off constant),
  * where they diverge, resync by locating a later unique 32-byte window,
  * every divergence/segment start/end is reported.

usage: app_map_walk.py <dump.bin> <dump_base_hex>
"""
import sys, hashlib, collections

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
f = open(APP, 'rb').read()
m = open(dump_path, 'rb').read()
FN, MN = len(f), len(m)
print("file 0x%x  dump 0x%x  base 0x%x  md5 %s" %
      (FN, MN, base, hashlib.md5(f).hexdigest()[:16]))

RUNAWAY = 1 << 20     # stop resyncing when we run past this

def resync(fo, lo, hi):
    """Find the smallest file offset >= fo (on a 512 grid) whose 32-byte window
    occurs in the dump inside [lo,hi). Returns (file_off, dump_off) or None."""
    step = 512
    start = (fo + step - 1) // step * step
    for cand in range(start, min(FN - 32, fo + RUNAWAY), step):
        w = f[cand:cand + 32]
        if w.count(w[0:1]) == 32:
            continue
        i = m.find(w, lo, hi)
        if i != -1:
            return cand, i
    return None

# seed: first file offset whose window is found in the dump
seed = None
for cand in range(0, min(FN - 32, RUNAWAY), 512):
    i = m.find(f[cand:cand + 32])
    if i != -1:
        seed = (cand, i)
        break
if seed is None:
    print("no seed found")
    sys.exit(1)
print("seed: file 0x%x <-> 0x%x (delta 0x%x)" % (seed[0], base + seed[1], base + seed[1] - seed[0]))

# walk forward in lockstep
segs = []            # (file_start, file_end, dump_start)
fo, mo = seed
seg_start_fo, seg_start_mo = fo, mo
# back up to the true start of this segment
while fo > 0 and mo > 0 and f[fo - 1] == m[mo - 1]:
    fo -= 1
    mo -= 1
seg_start_fo, seg_start_mo = fo, mo

last_report = 0
while fo < FN - 32 and mo < MN - 32:
    if f[fo] == m[mo]:
        fo += 1
        mo += 1
        continue
    segs.append((seg_start_fo, fo, seg_start_mo))
    nxt = resync(fo, mo, min(MN, mo + RUNAWAY))
    if nxt is None:
        print("  [stop] no resync after file 0x%x" % fo)
        break
    if fo - last_report > 0x4000 or True:
        pass
    print("  gap: file 0x%08x..0x%08x (%d bytes) not present 1:1;  runtime jumped "
          "0x%08x -> 0x%08x" % (fo, nxt[0], nxt[0] - fo, base + mo, base + nxt[1]))
    fo, mo = nxt
    while fo > 0 and mo > 0 and f[fo - 1] == m[mo - 1]:
        fo -= 1
        mo -= 1
    seg_start_fo, seg_start_mo = fo, mo

segs.append((seg_start_fo, fo, seg_start_mo))
print()
print("=== %d linear segments (file range -> runtime range, delta) ===" % len(segs))
tot = 0
for a, b, ds in segs:
    da, db = base + ds, base + ds + (b - a)
    tot += b - a
    print("  file 0x%08x-0x%08x (%7d B)  ->  0x%08x-0x%08x   delta=0x%08x" %
          (a, b, b - a, da, db, da - a))
print("total mapped 1:1: %d of %d (%.1f%%)" % (tot, FN, 100.0 * tot / FN))
