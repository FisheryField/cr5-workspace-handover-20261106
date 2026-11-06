#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag8: WHERE is the tool mesh actually attached in this station?
#  - tool.GeometryPose() (mesh attach pose relative to robot) vs section-9 ref
#    transl(0,0,159.5)*rotX(-90)
#  - transform exported STL local verts to BASE frame via the station chain,
#    print AABB (is the short end in front of the flange or behind?)
#  - engulf test at the mesh AABB center: Collision(tool,w), Collision(robot,w)
#  - exact restore
import sys, io, os, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl, rotx

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()

gp = tool.GeometryPose()
print("tool GeometryPose: pos", ["%.3f" % v for v in gp.Pos()])
for r in gp.rows[:3]:
    print("   ", ["%8.4f" % v for v in r[:3]])
print("section-9 ref: pos (0,0,159.500), rows [[1,0,0],[0,0,-1],[0,1,0]]-ish")

# STL local verts
p = os.path.join(r"D:\mydata\glm-workplace\tools", "diag8_tool_local.stl")
RDK.Save(p, tool)
data = open(p, "rb").read()
n = struct.unpack("<I", data[80:84])[0]
xs, ys, zs = [], [], []
off = 84
for i in range(n):
    vals = struct.unpack("<12fH", data[off:off+50])
    for t in range(3):
        xs.append(vals[3+3*t]); ys.append(vals[4+3*t]); zs.append(vals[5+3*t])
    off += 50
print("\nlocal STL: %d tris, x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"
      % (n, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

# mesh frame in BASE = B^-1 * (world of GeometryPose chain): for a tool child of
# robot, world = B * flange_pose * GeometryPose ; mesh-in-base = flange * gp
flange = robot.Pose()
mesh_in_base = flange * gp
pts = []
for x, y, z in [(min(xs),min(ys),min(zs)), (max(xs),max(ys),max(zs))]:
    pass
# full AABB: transform all 8 corners of local box
import itertools
from robodk.robomath import transl
corners = list(itertools.product([min(xs),max(xs)],[min(ys),max(ys)],[min(zs),max(zs)]))
wp = [(mesh_in_base * transl(*c)).Pos() for c in corners]
bx = [v[0] for v in wp]; by = [v[1] for v in wp]; bz = [v[2] for v in wp]
print("mesh AABB in BASE frame: x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"
      % (min(bx),max(bx),min(by),max(by),min(bz),max(bz)))
print("flange in base: (%.1f, %.1f, %.1f)" % tuple(v for v in flange.Pos()[:3]))
print("TCP   in base expected: (183.6, -673.2, 300.0)")

# engulf test at mesh AABB center
cx, cy, cz = (min(bx)+max(bx))/2, (min(by)+max(by))/2, (min(bz)+max(bz))/2
saved = w.PoseAbs()
inb = B.inv() * saved
w.setPoseAbs(B * transl(cx, cy, cz) * B.inv() * saved)
print("\nwheel engulfed at mesh center in-base (%.1f, %.1f, %.1f):" % (cx, cy, cz))
print("  Collision(tool, w) = %d   (1 expected if mesh really there)" % RDK.Collision(tool, w))
print("  Collision(robot, w) = %d  (robot-link pair sanity)" % RDK.Collision(robot, w))
w.setPoseAbs(saved)
print("restored wheel in-base: (%.2f, %.2f, %.2f)" % tuple(v for v in (B.inv()*w.PoseAbs()).Pos()[:3]))
