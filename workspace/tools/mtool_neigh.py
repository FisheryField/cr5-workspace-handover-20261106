#!/usr/bin/env python3
"""Print the string neighbourhood around the upgrade route tokens."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = open(os.path.join(ROOT, "data/mToolServer.bin"), "rb").read()
runs = [(m.start(), m.group().decode("ascii", "replace"))
        for m in re.finditer(rb"[\x20-\x7e]{3,}", data)]

ANCHORS = [0x074120,              # "singleFwAndXml"
           0x07887c,              # "updateFunc_CRSingleFwAndXml"
           0x07a5b8,              # /mToolServer/control/version.json
           0x079df4,              # /tmp/tUpdate/slave/readXml
           ]
for a in ANCHORS:
    print("=" * 78)
    print("neighbourhood of 0x%06x" % a)
    print("=" * 78)
    for off, s in runs:
        if a - 0x600 <= off <= a + 0x600:
            mark = " <<<" if off == a else ""
            print("  @0x%06x  %s%s" % (off, s[:140], mark))
    print()

# every string that looks like a route path
print("=" * 78)
print("all strings that could be a registered route")
print("=" * 78)
for off, s in runs:
    if re.match(r"^/[A-Za-z]", s) and "/home/" not in s and "SOEM" not in s \
            and not s.endswith((".cpp", ".c", ".h", ".json", ".txt", ".sh", ".log", ".gz", ".conf")):
        if re.search(r"[A-Z]", s) and "/" in s[1:]:
            print("  @0x%06x  %s" % (off, s[:140]))
