#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ask the RUNNING RoboDK instance for the Trace-related commands and their
allowed values (read-only).

RoboDK supports this directly: an empty RDK.Command("", "") returns every
command and its valid parameters (see Library/Scripts/ShowCommands.py).
"""
import os
import sys

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

RDK = Robolink()
print("RoboDK version :", RDK.Version())
print("RunMode        :", RDK.RunMode())

txt = RDK.Command("", "")
rows = []
for row in str(txt).replace("\r", "").split("\n"):
    cells = [c.strip() for c in row.replace("</td><td>", "\t").split("\t")]
    cells = [c for c in cells if c]
    if not cells:
        continue
    name = cells[0].replace("<td>", "").replace("</td>", "").strip()
    rows.append((name, cells))

print("\ntotal command rows:", len(rows))
for name, cells in rows:
    if "trace" in name.lower():
        print("  %-22s -> %s" % (name, " | ".join(cells[1:])[:160]))

print("\n--- current values ---")
for cmd in ("TraceStyle", "Trace_Render_Style"):
    try:
        print("  %-22s = %r" % (cmd, RDK.Command(cmd)))
    except Exception as e:  # noqa: BLE001
        print("  %-22s EXC %s" % (cmd, e))
