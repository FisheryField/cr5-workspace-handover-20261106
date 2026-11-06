#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Last probe: MoveL_Test (used by _linear_path_endpoint_uncached, guard != 0)
# with wheel-tool pair ON: does it catch the plunge?
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink, robomath

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
st = robot.ConnectedState()
if (st[0] if isinstance(st, tuple) else st) not in (-2, -1, 0):
    print("ABORT: driver connected"); sys.exit(2)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

wheel = RDK.Item("磨砂圆柱_R180_H40")
tool = robot.getLink(robolink.ITEM_TYPE_TOOL)
saved = robot.Joints().list()[:6]

poseA = robomath.xyzrpw_2_pose([0, -762.7, 300, -90, 0, 180])
poseProbe = robomath.xyzrpw_2_pose([0, -780.0, 300, -90, 0, 180])
jA = robot.SolveIK(poseA).list()

RDK.setCollisionActivePair(robolink.COLLISION_ON, tool, wheel)   # map: wheel ON
try:
    robot.setJoints(jA)
    status = robot.MoveL_Test(jA, poseProbe, minstep_mm=1)
    print("MoveL_Test (wheel-tool ON, plunge 17.3mm): status =", status,
          "(0=ok, negative=collision/unreachable)")
    pairs = RDK.CollisionPairs()
    print("pairs:", [(a.Name(), b.Name()) for a, b, _, _ in pairs])
finally:
    robot.setJoints(saved)
    RDK.setCollisionActivePair(robolink.COLLISION_OFF, tool, wheel)
print("restored:", [round(x, 3) for x in robot.Joints().list()[:6]])
