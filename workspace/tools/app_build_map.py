#!/usr/bin/env python3
"""Build the Application.app file-offset <-> runtime-address map (final).

The loader keeps the payload of the .app archive and drops per-record header /
pointer metadata, so the runtime image is ~3-5% smaller than the file and the
file/runtime delta drifts slowly.  The mapping is therefore piecewise linear.

Greedy alignment:
  * from the current (file, dump) position, advance while bytes agree;
  * at a mismatch, scan forward in the file for a window that also occurs
    forward in the dump, and score candidates by how many bytes agree on BOTH
    sides of the candidate boundary;
  * accept the best candidate if its score clears a threshold, otherwise skip
    the file byte and retry (bounded).

usage: app_build_map.py <dump[.gz]> <dump_base_hex> [out.json]
"""
import sys, gzip, json, hashlib, collections

APP = r"D:\mydata\workspace\data\Application.app"
W = 24                  # resync window
MAXSKIP = 0x8000        # how far in the file to look for the next resync
MAXMOVE = 0x8000        # how far in the dump
SCORE = 96              # bytes that must agree around a resync boundary
LOOKBACK = 512

f = open(APP, 'rb').read()
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
save = sys.argv[3] if len(sys.argv) > 3 else None
m = gzip.open(dump_path, 'rb').read() if dump_path.endswith('.gz') else open(dump_path, 'rb').read()
FN, MN = len(f), len(m)
print("file 0x%08x md5 %s / dump 0x%08x base 0x%08x" % (FN, hashlib.md5(f).hexdigest()[:16], MN, base))


def agree(a, b, limit):
    n = 0
    while n < limit and a + n < FN and b + n < MN and f[a + n] == m[b + n]:
        n += 1
    return n


def best_resync(fo, mo):
    best = None
    for d in range(1, MAXSKIP):
        cf = fo + d
        if cf + W > FN:
            break
        w = f[cf:cf + W]
        if w.count(w[0:1]) == W:
            continue
        i = idx.get(w)
        if i is None:
            continue
        if not (mo - LOOKBACK <= i < mo + MAXMOVE + d + 64):
            continue
        fwd = agree(cf, i, 4096)
        if fwd < SCORE:
            continue
        # look back
        back = 0
        while back < LOOKBACK and cf - back - 1 >= 0 and i - back - 1 >= 0 \
                and f[cf - back - 1] == m[i - back - 1]:
            back += 1
        score = fwd + back
        if best is None or score > best[0]:
            best = (score, cf, i, fwd, back)
            if score > 2048:
                break
    return best


runs, gaps = [], []
# index the dump: 4-byte-aligned 24-byte windows -> first offset, unique only
idx = {}
for i in range(0, MN - W, 4):
    w = m[i:i + W]
    if w in idx:
        idx[w] = None
    else:
        idx[w] = i
idx = {w: i for w, i in idx.items() if i is not None}
print("dump anchor index: %d unique %d-byte windows" % (len(idx), W))

seed = None
for cand in range(0, 0x40000, 4):
    w = f[cand:cand + 64]
    if w.count(w[0:1]) == 64:
        continue
    i = m.find(w)
    if i >= 0 and agree(cand, i, 512) == 512:
        seed = (cand, i)
        break
assert seed, "no seed"
fo, mo = seed
print("seed file 0x%08x <-> mem 0x%08x delta 0x%08x" % (fo, base + mo, base + mo - fo))
skip = 0
while fo < FN - W and mo < MN - W:
    s_fo, s_mo = fo, mo
    while fo < FN - W and mo < MN - W and f[fo] == m[mo]:
        fo += 1
        mo += 1
    if fo - s_fo >= 16:
        runs.append((s_fo, fo, s_mo))
    r = best_resync(fo, mo)
    if r is None:
        skip += 1
        if skip > 64:
            print("[stop] no resync after file 0x%08x mem 0x%08x" % (fo, base + mo))
            break
        fo += 1
        continue
    skip = 0
    score, nfo, nmo, fwd, back = r
    gaps.append((fo - back, nfo, nfo - fo, mo - back, nmo, nmo - mo, fwd, back))
    fo, mo = nfo, nmo
    if len(runs) % 300 == 0:
        sys.stderr.write("  runs=%d file=0x%08x mem=0x%08x\n" % (len(runs), fo, base + mo))

print()
tot = sum(b - a for a, b, _ in runs)
print("=== %d payload segments / %d resyncs, payload %d / %d (%.2f%%) ===" %
      (len(runs), len(gaps), tot, FN, 100.0 * tot / FN))
deltas = [(base + ds) - a for a, b, ds in runs]
print("delta 0x%08x .. 0x%08x (spread %d)" % (min(deltas), max(deltas), max(deltas) - min(deltas)))
mono = sum(1 for a, b in zip(runs, runs[1:]) if b[2] < a[2])
print("non-monotonic runtime starts: %d (should be 0)" % mono)
L = [b - a for a, b, _ in runs]
print("segment length: min %d median %d max %d" % (min(L), sorted(L)[len(L) // 2], max(L)))
h = collections.Counter(g[2] for g in gaps)
print("largest file skips:", h.most_common(6))

if save:
    json.dump({
        "app_md5": hashlib.md5(f).hexdigest(),
        "app_size": FN,
        "dump_base": base,
        "delta_const": 0x75a95cd0,
        "segments": [{"file_start": a, "file_end": b, "runtime_start": base + ds}
                     for a, b, ds in runs],
    }, open(save, 'w'), indent=1)
    print("wrote %s (%d segments)" % (save, len(runs)))
