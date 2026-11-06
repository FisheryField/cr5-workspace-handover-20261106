#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bs1.stp：解析 CIRCLE/CYLINDRICAL_SURFACE 半径（经 AXIS2_PLACEMENT_3D 解引用中心）。"""
import re, io

P = r"D:\mydata\working things\dobot_arm\2025.12\2025.12\bs1.stp"
txt = io.open(P, encoding="utf-8", errors="replace").read()

pts = {}
for m in re.finditer(r"#(\d+)\s*=\s*CARTESIAN_POINT\([^,]*,\s*\(([^)]*)\)\)", txt):
    try:
        pts[int(m.group(1))] = [float(x) for x in m.group(2).split(",")]
    except ValueError:
        pass

placements = {}
for m in re.finditer(r"#(\d+)\s*=\s*AXIS2_PLACEMENT_3D\([^,]*,\s*#(\d+)", txt):
    placements[int(m.group(1))] = int(m.group(2))

def center(pid):
    return pts.get(placements.get(pid))

print("== CIRCLE（按半径排序）==")
circles = []
for m in re.finditer(r"CIRCLE\('[^']*',\s*#(\d+),\s*([\d.E+-]+)\)", txt):
    pid, r = int(m.group(1)), float(m.group(2))
    c = center(pid)
    if c:
        circles.append((r, c))
for r, c in sorted(circles, key=lambda t: -t[0]):
    print("  R=%7.3f (D=%7.3f)  center=(%8.2f, %8.2f, %8.2f)" % (r, 2*r, c[0], c[1], c[2]))

print()
print("== CYLINDRICAL_SURFACE 半径 ==")
cyls = []
for m in re.finditer(r"CYLINDRICAL_SURFACE\('[^']*',\s*#(\d+),\s*([\d.E+-]+)\)", txt):
    pid, r = int(m.group(1)), float(m.group(2))
    c = center(pid)
    cyls.append((r, c if c else [0,0,0]))
for r, c in sorted(cyls, key=lambda t: -t[0]):
    print("  R=%7.3f (D=%7.3f)  axis@=(%8.2f, %8.2f, %8.2f)" % (r, 2*r, c[0], c[1], c[2]))
