#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect the running RoboDK's trace settings and snapshot the 3D view.

Read-only except for the optional Trace On/Off display toggle.
"""
import os
import sys

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)

RDK = Robolink()
print("version:", RDK.Version())

print("\n--- params containing 'race' ---")
try:
    for name, value in RDK.getParams():
        if "race" in name or "race" in str(value):
            print("   %-28s = %r" % (name, value))
except Exception as e:  # noqa: BLE001
    print("   getParams EXC", e)

print("\n--- known candidates (getParam) ---")
for key in ("Trace_Render_Style", "TraceStyle", "Trace_Render_Style_Default"):
    try:
        print("   %-28s = %r" % (key, RDK.getParam(key)))
    except Exception as e:  # noqa: BLE001
        print("   %-28s EXC %s" % (key, e))

print("\n--- items that look like a trace ---")
try:
    station = RDK.ActiveStation()
    for it in station.Childs():
        if "trace" in it.Name().lower() or "spray" in it.Name().lower():
            print("   item:", it.Name(), "type:", it.Type())
except Exception as e:  # noqa: BLE001
    print("   items EXC", e)

for tag in ("on", "off"):
    try:
        print("\nTrace %s ->" % tag, RDK.Command("Trace", tag))
    except Exception as e:  # noqa: BLE001
        print("Trace %s EXC %s" % (tag, e))

p = os.path.join(OUT, "snap_%s.png" % sys.argv[1] if len(sys.argv) > 1 else "snap.png")
try:
    r = RDK.Cam2D_Snapshot(p, None)
    print("\nsnapshot ->", r, "exists:", os.path.exists(p),
          "size:", os.path.getsize(p) if os.path.exists(p) else 0)
except Exception as e:  # noqa: BLE001
    print("\nsnapshot EXC", e)
