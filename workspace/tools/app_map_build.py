#!/usr/bin/env python3
"""Build an exact file-offset <-> runtime-address map for CODESYS Application.app.

Method
------
Walk the file and the process dump together.  Inside a mapped run the two
advance in lockstep (runtime = file_off + delta).  At a divergence, look for the
next file window that appears in the dump with the smallest forward jump, and
verify it by walking on; only accept a resync when the following bytes agree for
a while.  Every accepted run is a segment of the mapping.

usage: app_map_build.py <dump[.gz]> <dump_base_hex> [out.json]
"""
import sys, os, gzip, json, hashlib, struct, collections

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
out_path = sys.argv[3] if len(sys.argv) > 3 else None

f = open(APP, 'rb').read()
if dump_path.endswith('.gz'):
    m = gzip.open(dump_path, 'rb').read()
else:
    m = open(dump_path, 'rb').read()
FN, MN = len(f), len(m)
print("file  0x%08x bytes  md5 %s" % (FN, hashlib.md5(f).hexdigest()))
print("dump  0x%08x bytes  base 0x%08x  %s" % (MN, base, dump_path))

VERIFY = 192          # bytes that must agree before a resync is accepted
MAXJUMP = 1 << 20     # max forward memory jump per resync


def try_resync(fo, mo_start):
    """Return (file_off, dump_off) for the best resync at or after file fo."""
    best = None
    lo = mo_start
    hi = min(MN, mo_start + MAXJUMP)
    # scan candidate file offsets; use 16-byte windows for uniqueness
    step = 8
    for cand in range(fo, min(FN - 32, fo + 0x20000), step):
        w = f[cand:cand + 16]
        if w.count(w[0:1]) == 16:
            continue
        i = m.find(w, lo, hi)
        if i == -1:
            continue
        # verify the continuation
        n = min(VERIFY, FN - cand, MN - i)
        if f[cand:cand + n] == m[i:i + n]:
            score = (cand - fo) * 1 + (i - mo_start) * 1
            if best is None or score < best[0]:
                best = (score, cand, i)
            if best is not None and cand - fo < 0x40 and i - mo_start < 0x40:
                break
    if best is None:
        return None
    return best[1], best[2]


runs = []          # (file_start, file_end, dump_off)
fo = mo = None

# seed: first file window found anywhere in the dump
seed = None
for cand in range(0, min(FN - 32, 1 << 20), 64):
    w = f[cand:cand + 32]
    if w.count(w[0:1]) == 32:
        continue
    i = m.find(w)
    if i != -1:
        seed = (cand, i)
        break
assert seed, "no seed"
fo, mo = seed
print("seed file 0x%08x <-> 0x%08x (delta 0x%08x)" % (fo, base + mo, base + mo - fo))

while fo < FN - 32 and mo < MN - 32:
    # grow a lockstep run
    s_fo, s_mo = fo, mo
    while fo < FN - 32 and mo < MN - 32 and f[fo] == m[mo]:
        fo += 1
        mo += 1
    runs.append((s_fo, fo, s_mo))
    nxt = try_resync(fo, mo)
    if nxt is None:
        print("  [stop] no resync after file 0x%08x (mem 0x%08x)" % (fo, base + mo))
        break
    nfo, nmo = nxt
    if nfo - fo > 0x20000:
        print("  [stop] resync jump too far: file 0x%08x -> 0x%08x" % (fo, nfo))
        break
    fo, mo = nfo, nmo

runs.sort()
print()
print("=== %d lockstep runs ===" % len(runs))
tot = 0
for a, b, ds in runs[:400]:
    da = base + ds
    tot += b - a
    print("  file 0x%08x-0x%08x (%8d B) -> 0x%08x-0x%08x  delta 0x%08x" %
          (a, b, b - a, da, da + (b - a), da - a))
print("mapped 1:1 total: %d / %d (%.2f%%)" % (tot, FN, 100.0 * tot / FN))

if out_path:
    tbl = [{"file_start": a, "file_end": b, "runtime_start": base + ds,
            "delta": (base + ds) - a} for a, b, ds in runs]
    json.dump({"app_md5": hashlib.md5(f).hexdigest(), "file_size": FN,
               "dump_base": base, "segments": tbl}, open(out_path, 'w'), indent=1)
    print("wrote %s (%d segments)" % (out_path, len(tbl)))
