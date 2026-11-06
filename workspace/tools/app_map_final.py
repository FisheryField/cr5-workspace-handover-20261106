#!/usr/bin/env python3
"""Build the Application.app file-offset <-> runtime-address map.

The file is an *archive* of records; the loader keeps the payload and drops the
per-record headers, so the runtime image is ~3% smaller than the file.  This
walks the file and the dump in lockstep, and at every mismatch searches for the
resync point, recording the payload segments of the mapping.

usage: app_map_final.py <dump[.gz]> <dump_base_hex> [save.json]
"""
import sys, gzip, json, hashlib

APP = r"D:\mydata\workspace\data\Application.app"
W = 24                 # window used for resync uniqueness
CHECK = 256            # bytes that must agree to accept a resync
SEARCH_F = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x4000   # file resync range
SEARCH_M = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0x4000   # memory resync range

f = open(APP, 'rb').read()
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
save = sys.argv[3] if len(sys.argv) > 3 else None
m = gzip.open(dump_path, 'rb').read() if dump_path.endswith('.gz') else open(dump_path, 'rb').read()
FN, MN = len(f), len(m)
print("file 0x%08x md5 %s / dump 0x%08x base 0x%08x" %
      (FN, hashlib.md5(f).hexdigest()[:16], MN, base))

def find_resync(fo, mo):
    """smallest (file_off, dump_off) with matching content after fo/mo,
    with dump_off required to move forward (the image is laid out in order)."""
    cands = []
    for d in range(1, SEARCH_F):
        cf = fo + d
        w = f[cf:cf + W]
        if len(w) < W or w.count(w[0:1]) == W:
            continue
        lo = mo + 1
        hi = min(MN, mo + SEARCH_M)
        if lo >= hi:
            return None
        i = m.find(w, lo, hi)
        if i < 0:
            continue
        n = min(CHECK, FN - cf, MN - i)
        if f[cf:cf + n] == m[i:i + n]:
            cands.append((cf, i))
            if len(cands) >= 4:
                break
    if not cands:
        return None
    # prefer the smallest forward memory move, then the smallest file move
    cands.sort(key=lambda t: ((t[1] - mo), (t[0] - fo)))
    return cands[0]

runs = []
gaps = []
# seed on a long verbatim stretch
seed = None
for cand in range(0, 0x40000, 4):
    w = f[cand:cand + W]
    if w.count(w[0:1]) == W:
        continue
    i = m.find(w)
    if i >= 0 and f[cand:cand + 256] == m[i:i + 256]:
        seed = (cand, i)
        break
assert seed
fo, mo = seed
print("seed file 0x%08x <-> mem 0x%08x (delta 0x%08x)" % (fo, base + mo, base + mo - fo))

while fo < FN - W and mo < MN - W:
    s_fo, s_mo = fo, mo
    while fo < FN - W and mo < MN - W and f[fo] == m[mo]:
        fo += 1
        mo += 1
    if fo > s_fo:
        runs.append((s_fo, fo, s_mo))
    r = find_resync(fo, mo)
    if r is None:
        print("[stop] no resync after file 0x%08x mem 0x%08x" % (fo, base + mo))
        break
    nfo, nmo = r
    gaps.append((fo, nfo, nfo - fo, mo, nmo, nmo - mo))
    fo, mo = nfo, nmo
    if len(runs) % 200 == 0:
        sys.stderr.write("  .. file 0x%08x mem 0x%08x runs=%d\n" % (fo, base + mo, len(runs)))

print()
print("=== %d payload segments, %d archive records dropped ===" % (len(runs), len(gaps)))
tot = sum(b - a for a, b, _ in runs)
print("payload bytes: %d / %d (%.2f%%)" % (tot, FN, 100.0 * tot / FN))
# delta statistics
import statistics
deltas = [(base + ds) - a for a, b, ds in runs]
print("delta min 0x%08x max 0x%08x spread %d bytes" %
      (min(deltas), max(deltas), max(deltas) - min(deltas)))
print("record length histogram (file bytes dropped):")
import collections
h = collections.Counter(g[2] for g in gaps)
for k, n in h.most_common(12):
    print("   %5d bytes x%d" % (k, n))
print()
print("=== first 40 segments ===")
for a, b, ds in runs[:40]:
    print("  file 0x%08x-0x%08x (%6d B) -> mem 0x%08x  delta 0x%08x" %
          (a, b, b - a, base + ds, (base + ds) - a))
print()
print("=== first 30 dropped records ===")
for a, b, ln, ma, mb, mln in gaps[:30]:
    print("  file 0x%08x..0x%08x (%3d B) mem 0x%08x..0x%08x (%3d B)" %
          (a, b, ln, base + ma, base + mb, mln))

if save:
    json.dump({
        "app_md5": hashlib.md5(f).hexdigest(),
        "file_size": FN,
        "dump_base": base,
        "segments": [{"file_start": a, "file_end": b, "runtime_start": base + ds}
                     for a, b, ds in runs],
        "dropped": [{"file_start": a, "file_end": b, "runtime_start": base + ma}
                    for a, b, _, ma, _, _ in gaps],
    }, open(save, 'w'), indent=1)
    print("wrote %s" % save)
