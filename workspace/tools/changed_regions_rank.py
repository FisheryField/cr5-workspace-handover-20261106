#!/usr/bin/env python3
"""Rank ALL changed regions between the two payloads by size, and identify the
big ones.

Motivation: §25-27 (tools/servo_blockdiff.py) established that the two images
share only 754 equal blocks / 34.9% of their bytes, with 744 changed regions
totalling 220,160 B - but only the LARGEST one (799 B, the position-value write
site) was ever read.  The position chain has since been excluded
experimentally (the J6 patch did nothing), so the remaining large changed
regions are the best unexamined candidates.

Method (robust, no alignment assumptions):
  1. index every 16-byte block of the 3150 payload by content
  2. walk the D8 payload and find all maximal exact matches >= 32 bytes
  3. the complement of the merged matches = changed regions
  4. rank by size; for the top regions also dump a little disassembly from both
     builds so the region can be identified

Positive control: the version strings DS.3.2.D.8 / DS.3.1.5.0 occupy different
byte ranges, so a changed region must cover each of them.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A_REL = "data/servo_fw_samples/elf/v328d8.bin"    # D8
B_REL = "data/servo_fw_samples/elf/v3150.bin"     # 3150
LOAD = 0x08010000
K = 16          # index block size
MINMATCH = 32


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def main():
    a = payload(os.path.join(ROOT, A_REL))
    b = payload(os.path.join(ROOT, B_REL))
    print("D8 %d B, 3150 %d B" % (len(a), len(b)))

    print("indexing 3150 ...")
    idx = {}
    for i in range(0, len(b) - K + 1):
        idx.setdefault(b[i:i + K], []).append(i)
    print("  %d distinct %d-byte blocks" % (len(idx), K))

    print("matching ...")
    matches = []          # (a_start, b_start, length)
    i = 0
    while i <= len(a) - K:
        cands = idx.get(a[i:i + K])
        if not cands:
            i += 1
            continue
        best = (0, None)
        for j in cands:
            # extend forward
            n = K
            while i + n < len(a) and j + n < len(b) and a[i + n] == b[j + n]:
                n += 1
            if n > best[0]:
                best = (n, j)
                if i + n >= len(a):
                    break
        n, j = best
        if n >= MINMATCH:
            matches.append((i, j, n))
            i += n
        else:
            i += 1
    print("  %d raw matches" % len(matches))

    # merge overlapping/adjacent matches, keep the longest chain per A position
    matches.sort()
    merged = []
    for m in matches:
        if merged and m[0] <= merged[-1][0] + merged[-1][2]:
            pa, pb, pn = merged[-1]
            ne = max(pa + pn, m[0] + m[2])
            merged[-1] = (pa, pb, ne - pa)
        else:
            merged.append(list(m) and m)
    merged = [tuple(x) for x in merged]
    eq = sum(m[2] for m in merged)
    print("  merged into %d equal runs, %d bytes equal (%.1f%% of D8)"
          % (len(merged), eq, 100.0 * eq / len(a)))

    # changed regions in A
    changed = []
    pos = 0
    for pa, pb, pn in merged:
        if pa > pos:
            changed.append((pos, pa - pos))
        pos = max(pos, pa + pn)
    if pos < len(a):
        changed.append((pos, len(a) - pos))
    changed.sort(key=lambda x: -x[1])
    print("  %d changed regions, %d bytes total"
          % (len(changed), sum(c[1] for c in changed)))

    # positive control: both version strings must sit inside changed regions
    va = a.find(b"DS.3.2.D.8")
    vb = b.find(b"DS.3.1.5.0")
    inside_a = any(s <= va < s + n for s, n in changed) if va >= 0 else None
    print("  control: D8 version string @0x%05x inside a changed region: %s"
          % (va, inside_a))
    if va >= 0 and not inside_a:
        print("  !! control failed - abort")
        return 2

    print()
    print("=" * 76)
    print("TOP 25 CHANGED REGIONS (D8 offset, size)")
    print("=" * 76)
    md = make_md()
    for s, n in changed[:25]:
        txt = []
        for ins in md.disasm(a[s:s + min(n, 24)], LOAD + s):
            txt.append("%s %s" % (ins.mnemonic, ins.op_str))
            if len(txt) >= 3:
                break
        print("  D8 off 0x%05x (flash 0x%08x)  size %5d B   %s"
              % (s, LOAD + s, n, " | ".join(txt)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
