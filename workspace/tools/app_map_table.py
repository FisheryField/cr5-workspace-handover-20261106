#!/usr/bin/env python3
"""Build the Application.app file-offset <-> runtime-address map table.

A mapping run is a (file_start, file_end, delta) triple with
    runtime_addr = file_off + delta
verified by re-reading the live dump.  Anchors come from the application's own
ASCII string/symbol table (the only content that survives loading both verbatim
and in known positions), each grown in both directions to the true run bounds.

usage: app_map_table.py <dump[.gz]> <dump_base_hex> [out.json]
"""
import sys, gzip, json, re, hashlib

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
out = sys.argv[3] if len(sys.argv) > 3 else r"D:\mydata\workspace\data\appmap\app_map.json"

f = open(APP, 'rb').read()
m = gzip.open(dump_path, 'rb').read() if dump_path.endswith('.gz') else open(dump_path, 'rb').read()
FN, MN = len(f), len(m)
print("file 0x%08x md5 %s / dump 0x%08x base 0x%08x" %
      (FN, hashlib.md5(f).hexdigest()[:16], MN, base))

# The loaded Application image is one contiguous anonymous extent; restrict all
# anchors to it so heap/stack copies of the same strings cannot confuse the map.
IMG_LO = 0x75a70000
IMG_HI = 0x75d00000
print("image extent searched: 0x%08x..0x%08x" % (IMG_LO, IMG_HI))


GAP = 64            # tolerate small replaced regions (relocated pointers) inside a run


def agrees(fa, da, n):
    if fa + n > FN or da + n > MN:
        return False
    return f[fa:fa + n] == m[da:da + n]


def run_bounds(fo, do):
    """grow a candidate (file_off, dump_off) pair to the maximal run, tolerating
    short gaps of replaced bytes (relocation sites).
    Returns (file_start, file_end, delta, replaced_byte_count)."""
    G = 16          # bytes that must agree to accept a resync
    g = 0
    a, b = fo, do
    while a > 0 and b > 0:
        if f[a - 1] == m[b - 1]:
            a -= 1
            b -= 1
            continue
        found = False
        for k in range(1, GAP):
            if a - k < 0 or b - k < 0:
                break
            if f[a - k] == m[b - k] and agrees(a - k, b - k, G):
                g += k
                a -= k
                b -= k
                found = True
                break
        if not found:
            break
    e1, e2 = fo, do
    while e1 < FN and e2 < MN:
        if f[e1] == m[e2]:
            e1 += 1
            e2 += 1
            continue
        found = False
        for k in range(1, GAP):
            if e1 + k >= FN or e2 + k >= MN:
                break
            if f[e1 + k] == m[e2 + k] and agrees(e1 + k, e2 + k, G):
                g += k
                e1 += k
                e2 += k
                found = True
                break
        if not found:
            break
    return a, e1, (base + do) - fo, g


anchors = []
for mt in re.finditer(rb'[\x20-\x7e]{12,}', f):
    s = mt.group()[:96]
    if s.count(s[0:1]) == len(s):
        continue
    i = m.find(s)
    while i != -1:
        addr = base + i
        if IMG_LO <= addr < IMG_HI:          # only the Application image itself
            anchors.append((mt.start(), i))
        i = m.find(s, i + 1)
print("anchors (file string / dump occurrence pairs): %d" % len(anchors))

runs = []
for fo, do in anchors:
    a, e, d, g = run_bounds(fo, do)
    if e - a >= 48:
        runs.append((a, e, d))

# merge runs with identical delta that overlap, keeping the longest gap-aware run
best = {}
for a, b, d in runs:
    k = (d,)
    if k not in best or (b - a) > (best[k][1] - best[k][0]):
        best[k] = (a, b, d)
runs = sorted(best.values())
merged = []
for a, b, d in runs:
    if merged and merged[-1][2] == d and a <= merged[-1][1]:
        merged[-1] = (merged[-1][0], max(b, merged[-1][1]), d)
    else:
        merged.append((a, b, d))

# validate strictly
valid, rejected = [], 0
for a, b, d in merged:
    do = (a + d) - base                    # dump offset of file offset a
    if do < 0 or do + (b - a) > MN:
        rejected += 1
        continue
    # require the run to be mostly identical, and identical at both ends
    seg_f, seg_m = f[a:b], m[do:do + (b - a)]
    same = sum(1 for x, y in zip(seg_f, seg_m) if x == y)
    if same < 0.85 * (b - a) or seg_f[:8] != seg_m[:8]:
        rejected += 1
        continue
    valid.append((a, b, d, b - a - same))
valid.sort()
tot = sum(b - a for a, b, _, _ in valid)
print("runs: %d raw / %d merged / %d valid (rejected %d)" % (len(runs), len(merged), len(valid), rejected))
print("mapped 1:1: %d / %d bytes (%.2f%%)" % (tot, FN, 100.0 * tot / FN))

# coverage of the file
cov = bytearray(FN)
for a, b, _, _ in valid:
    for i in range(a, b):
        cov[i] = 1
print("byte coverage: %d (%.2f%%)" % (sum(cov), 100.0 * sum(cov) / FN))

print()
print("=== mapping runs (file -> runtime, delta) ===")
for a, b, d, _g in valid:
    print("  file 0x%08x-0x%08x (%6d B) -> 0x%08x-0x%08x  delta 0x%08x" %
          (a, b, b - a, a + d, b + d, d))

# pool summary: how many distinct deltas, and what runtime span each covers
pools = {}
for a, b, d, _g in valid:
    if d not in pools:
        pools[d] = [a, b]
    else:
        pools[d][0] = min(pools[d][0], a)
        pools[d][1] = max(pools[d][1], b)
print()
print("=== %d distinct delta pools ===" % len(pools))
for d, (a, b) in sorted(pools.items(), key=lambda kv: kv[0]):
    print("  delta 0x%08x  file 0x%08x..0x%08x  runtime 0x%08x..0x%08x" %
          (d, a, b, a + d, b + d))

json.dump({
    "app_md5": hashlib.md5(f).hexdigest(),
    "app_size": FN,
    "dump_base": base,
    "segments": [{"file_start": a, "file_end": b, "runtime_start": a + d,
                  "delta": d, "replaced_bytes": g} for a, b, d, g in valid],
}, open(out, 'w'), indent=1)
print("\nwrote %s (%d runs)" % (out, len(valid)))
