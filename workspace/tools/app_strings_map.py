#!/usr/bin/env python3
"""Extract ASCII string runs from Application.app and locate each one in a
runtime memory dump (both ASCII and UTF-16LE forms).

This is both an independent check of the file->runtime mapping and the fastest
way to find the PLC symbol name table in the live image.

usage: app_strings_map.py <dump[.gz]> <dump_base_hex> [minlen]
"""
import sys, gzip, re, json, collections

APP = r"D:\mydata\workspace\data\Application.app"
dump_path = sys.argv[1]
base = int(sys.argv[2], 16)
MINLEN = int(sys.argv[3]) if len(sys.argv) > 3 else 10

f = open(APP, 'rb').read()
m = gzip.open(dump_path, 'rb').read() if dump_path.endswith('.gz') else open(dump_path, 'rb').read()
print("file 0x%08x / dump 0x%08x base 0x%08x" % (len(f), len(m), base))

# strings in the file
strs = []
for mt in re.finditer(rb'[\x20-\x7e]{%d,}' % MINLEN, f):
    s = mt.group()
    if len(s) > 256:
        s = s[:256]
    strs.append((mt.start(), s))
print("file strings >= %d chars: %d" % (MINLEN, len(strs)))

def search(want):
    """return list of dump offsets where `want` occurs (cap 4)"""
    out = []
    i = m.find(want)
    while i != -1 and len(out) < 4:
        out.append(i)
        i = m.find(want, i + 1)
    return out

rows = []
n_ascii = n_utf16 = n_none = 0
delta_ascii = collections.Counter()
for off, s in strs:
    a = search(s)
    u = search(s.decode('ascii').encode('utf-16-le'))
    marker = 'both' if (a and u) else ('ascii' if a else ('utf16' if u else 'none'))
    if a:
        n_ascii += 1
        for x in a:
            delta_ascii[base + x - off] += 1
    if u:
        n_utf16 += 1
    if not a and not u:
        n_none += 1
    rows.append({"file_off": off, "s": s.decode('ascii', 'replace'),
                 "ascii": [base + x for x in a], "utf16": [base + x for x in u],
                 "kind": marker})

print("ascii hits %d / utf16 hits %d / no hit %d" % (n_ascii, n_utf16, n_none))
print()
print("=== delta histogram for ASCII hits (runtime - file_off) ===")
for d, n in delta_ascii.most_common(12):
    print("   0x%08x  x%d" % (d, n))
print()
print("=== sample of mapped strings (first 40 that hit) ===")
shown = 0
for r in rows:
    if r['kind'] == 'none':
        continue
    print("  file 0x%06x %-8s %-46r -> %s" %
          (r['file_off'], r['kind'], r['s'][:44],
           " ".join("0x%08x" % x for x in (r['ascii'] or r['utf16'])[:2])))
    shown += 1
    if shown >= 40:
        break

out = r"D:\mydata\workspace\data\appmap\app_strings.json"
json.dump(rows, open(out, 'w'), indent=1)
print("\nwrote %s" % out)
