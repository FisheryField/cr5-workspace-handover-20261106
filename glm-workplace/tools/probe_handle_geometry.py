#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Read-only mesh pull v2: GetPoints(FEATURE_OBJECT_MESH) returns (pts, name);
# pts rows are [x,y,z,nx,ny,nz] in OBJECT frame. Dump positions only.
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
toolT = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
print("tool valid:", toolT.Valid())

res = toolT.GetPoints(FEATURE_OBJECT_MESH)
pts, fname = res if isinstance(res, tuple) and len(res) == 2 else (res, "?")
n = len(pts)
print("feature:", fname, " vertex count:", n)
P = [(p[0], p[1], p[2]) for p in pts]
xs = [q[0] for q in P]; ys = [q[1] for q in P]; zs = [q[2] for q in P]
print("bbox obj-frame: x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]"
      % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
with open(r"D:\mydata\glm-workplace\tools\handle_vertices.json", "w", encoding="utf-8") as f:
    json.dump({"n": n, "pts": P}, f)
print("dumped -> tools/handle_vertices.json")

# tool geometry pose relative to its parent (robot flange): where mesh frame sits
gp = toolT.GeometryPose()
print("GeometryPose (mesh frame in parent frame):\n", gp)
print("robot PoseTool:", robot.PoseTool())

for nm in ('磨砂圆柱_R180_H40', '安装台_650x650x80mm', '地面_禁止穿越'):
    o = RDK.Item(nm, ITEM_TYPE_OBJECT)
    if o.Valid():
        pos = o.GeometryPose().Pos()
        print("%s GeometryPos: (%.2f, %.2f, %.2f)" % (nm, *pos))
    else:
        print(nm, "NOT FOUND")

print("current joints (info):", ["%.2f" % v for v in robot.Joints().list()[:6]])
