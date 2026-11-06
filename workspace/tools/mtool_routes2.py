#!/usr/bin/env python3
"""Extract NUL-terminated ASCII strings from mToolServer.bin and report the
upgrade-related HTTP surface, so the on-site flashing procedure can be exact.

(An earlier inline attempt used re.search on every offset and therefore returned
overlapping suffixes of the same string - it looked like it found 'type_info'
matches because 'infoeq' appeared inside them.  Proper NUL-delimited extraction
fixes that.)
"""
import re

P = "data/mToolServer.bin"
b = open(P, "rb").read()

# proper NUL-terminated string extraction
strings = []
cur = bytearray()
for ch in b:
    if 32 <= ch < 127:
        cur.append(ch)
    else:
        if len(cur) >= 4:
            strings.append(cur.decode("ascii"))
        cur = bytearray()
if len(cur) >= 4:
    strings.append(cur.decode("ascii"))

print("file %s : %d bytes, %d strings (len>=4)" % (P, len(b), len(strings)))

ROUTE = re.compile(r"^/[A-Za-z0-9_./{}-]+$")
hits = [s for s in strings if ROUTE.match(s)]
print()
print("=== route-like strings (%d) ===" % len(hits))
for s in sorted(set(hits)):
    print("   ", s)

print()
print("=== strings mentioning Fw / firmware / update / FoE / foe ===")
seen = set()
for s in strings:
    if re.search(r"Fw|firmware|update|FoE|foe|\.bin|\.xml", s) and s not in seen:
        seen.add(s)
        if len(s) < 200:
            print("   ", s)
    if len(seen) > 60:
        break
