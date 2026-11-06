#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List what is currently visible in the running RoboDK station.

Goal: find which item produces the yellow/green/blue multi-colour "trajectory"
(typically a visible Program path - RoboDK colours program path segments by
move type), and what trace settings are active.
Read-only.
"""
import os
import sys

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

TYPE_NAMES = {
    1: "Station", 2: "Robot", 3: "Frame", 4: "Tool", 5: "Object",
    6: "Target", 7: "Program", 8: "Instruction", 9: "Curve",
    10: "Points", 11: "Camera", 12: "Notes", 13: "Machine",
    14: "BallbarValidation", 15: "PathValidation", 16: "Tool",
}

RDK = Robolink()
station = RDK.ActiveStation()
print("station:", station.Name())
print("run mode:", RDK.RunMode(), "(1=simulate)")

print("\n%-34s %-10s %-8s %s" % ("NAME", "TYPE", "VISIBLE", "extra"))
print("-" * 78)
for it in station.Childs():
    t = it.Type()
    tname = TYPE_NAMES.get(t, "type%d" % t)
    try:
        vis = it.Visible()
    except Exception:  # noqa: BLE001
        vis = "?"
    extra = ""
    if tname == "Program":
        try:
            extra = "instructions=%d" % len(it.Childs())
        except Exception:  # noqa: BLE001
            pass
    if tname in ("Object", "Curve", "Points", "Program"):
        for key in ("Color", "DisplayCurvePoints", "SizeCurvePoints"):
            try:
                v = it.getParam(key)
                if v is not None:
                    extra += " %s=%s" % (key, v)
            except Exception:  # noqa: BLE001
                pass
    print("%-34s %-10s %-8s %s" % (it.Name()[:34], tname, vis, extra))

print("\n--- trace-related settings ---")
for k in ("Trace_Render_Style",):
    try:
        print("   %-24s = %r" % (k, RDK.getParam(k)))
    except Exception as e:  # noqa: BLE001
        print("   %-24s EXC %s" % (k, e))
