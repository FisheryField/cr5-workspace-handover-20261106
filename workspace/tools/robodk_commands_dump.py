#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump RoboDK's own command list (RDK.Command("", "")) and print every entry
whose name or values mention trace/path - this is the authoritative list of
Command() names and their accepted values.
"""
import io
import os
import re
import sys

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)

RDK = Robolink()
txt = str(RDK.Command("", ""))
raw = os.path.join(OUT, "robodk_commands_raw.txt")
with io.open(raw, "w", encoding="utf-8") as f:
    f.write(txt)
print("raw length:", len(txt), "->", raw)

# the table is html-ish with tabs / <br>; normalise and print trace rows
norm = txt.replace("&nbsp;", " ").replace("<br>", "\n").replace("</td><td>", "\t")
norm = re.sub(r"<[^>]+>", "", norm)
rows = [r.strip() for r in norm.split("\n") if r.strip()]
print("rows:", len(rows))
for r in rows:
    if re.search(r"trace|path|spray", r, re.I):
        print("   " + r.replace("\t", " | ")[:220])

print("\n--- raw context around 'Trace' ---")
for m in list(re.finditer(r"Trace", txt))[:6]:
    print(repr(txt[max(0, m.start() - 120):m.start() + 200]))
    print()
