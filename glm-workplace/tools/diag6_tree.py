#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag6: tree structure + is the wheel invisible ONLY to robot items?
#  1) print parents of wheel/table/floor/tool/base
#  2) temp world-translate wheel to engulf the TABLE, test Collision(w,table)
#  3) exact restore
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
floor = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

def par(it):
    p = it.Parent()
    return p.Name() if p.Valid() else "(station root)"

print("parents:")
for it, tag in [(w,'wheel'), (table,'table'), (floor,'floor'), (tool,'tool'), (robot,'robot')]:
    try:
        print("  %-6s -> %s" % (tag, par(it)))
    except Exception as e:
        print("  %-6s -> err %s" % (tag, e))

print("\nengulf test: wheel -> onto table center (world delta translation)")
saved = w.PoseAbs()
tw = table.PoseAbs()
wpos = saved.Pos()
delta = (tw.Pos()[0]-wpos[0], tw.Pos()[1]-wpos[1], 40.0-wpos[2])
w.setPoseAbs(transl(*delta) * saved)
print("  wheel now at world: (%.1f, %.1f, %.1f)" % tuple(v for v in w.PoseAbs().Pos()[:3]))
print("  Collision(wheel, table) = %d   (1 expected if engine sees the wheel)" % RDK.Collision(w, table))
print("  Collision(wheel, floor) = %d" % RDK.Collision(w, floor))
print("  Collision(wheel, tool ) = %d   (robot item - self-pair skip test)" % RDK.Collision(w, tool))

w.setPoseAbs(saved)
print("\nrestored wheel world: (%.2f, %.2f, %.2f)" % tuple(v for v in w.PoseAbs().Pos()[:3]))
