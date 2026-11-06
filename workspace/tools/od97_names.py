#!/usr/bin/env python3
"""Are the servo's 97 EtherCAT-reachable objects all standard CiA402, or do any
vendor (0x2xxx) objects appear?  This decides whether a vendor parameter like
H0C.02 / H01.17 can be reached by SDO at all.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
od = json.load(open(os.path.join(ROOT, "data/servo_fw_samples/od_328d8.json"),
                    encoding="utf-8"))
print("97-object metadata table: %d records" % len(od))
print()
names = [r["name"] for r in od]
print("all 97 names:")
for i, r in enumerate(od):
    print("  %2d  %-34s type=%-4s bits=%-3s attr=%-3s access=%-3s std_index=%s"
          % (i, r["name"], r.get("type"), r.get("bits"), r.get("attr"),
             r.get("access"), r.get("std_index")))

print()
pat = re.compile(r"\bH[0-9A-F]{2}\.[0-9]{2}\b")
hits = [n for n in names if pat.search(n)]
print("names that look like vendor H-codes : %d %s" % (len(hits), hits[:10]))
print("names containing any hex index like 0x2xxx : %s"
      % [n for n in names if re.search(r"0x2[0-9A-Fa-f]{3}", n)][:10])

hp = json.load(open(os.path.join(ROOT, "data/servo_fw_samples/hparam_map.json"),
                    encoding="utf-8"))
mi = [e["map_index"] for e in hp]
print()
print("hparam_map: %d entries, map_index range %d..%d"
      % (len(hp), min(mi), max(mi)))
# how does hparam encode the EtherCAT index?
print("sample entry: %s"
      % json.dumps({k: hp[39][k] for k in hp[39]
                    if k in ("para_index", "group", "sub", "map_index", "name")},
                   ensure_ascii=False).encode("ascii", "replace").decode("ascii"))
print("H01.17 entry: %s"
      % json.dumps({k: hp[39][k] for k in hp[39]
                    if k in ("para_index", "group", "sub", "map_index")},
                   ensure_ascii=False))
