#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag12 (smoking gun): import a COPY of the tool STL and place it in EXACT
# overlap with the tool itself (identical world pose = perfect mesh-mesh
# intersection). Also tool-copy vs table at same spot (mesh vs native).
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)

# tool mesh world transform = B * flange * GeometryPose
B = robot.Parent().PoseAbs()
flange = robot.Pose()
gp = tool.GeometryPose()
mesh_world = B * flange * gp
print("tool mesh world pose pos:", ["%.1f" % v for v in mesh_world.Pos()])

stl = r"D:\mydata\glm-workplace\tools\diag8_tool_local.stl"
copy = RDK.AddFile(stl)
copy.setName('mesh_overlap_test')
# exact overlap: same world pose as the tool mesh
copy.setPoseAbs(mesh_world)
print("copy world pos:", ["%.1f" % v for v in copy.PoseAbs().Pos()])

print("Collision(tool, toolcopy)  = %d   (1 expected; 0 => mesh-mesh broken)" % RDK.Collision(tool, copy))
print("Collision(copy, table)     = %d" % RDK.Collision(copy, table))
print("Collision(robot, toolcopy) = %d" % RDK.Collision(robot, copy))

# positive control: shove the copy into the table
t_pos = table.PoseAbs().Pos()
c_pos = copy.PoseAbs().Pos()
copy.setPoseAbs(transl(t_pos[0]-c_pos[0], t_pos[1]-c_pos[1], 40.0-c_pos[2]) * copy.PoseAbs())
print("copy shoved into table: Collision(copy, table) = %d  (1 expected)" % RDK.Collision(copy, table))
copy.Delete()
print("(test copy deleted)")
