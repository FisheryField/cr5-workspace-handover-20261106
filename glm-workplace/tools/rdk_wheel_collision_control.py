#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Control probe: same plunge path, but with wheel EXPLICITLY enabled in the
# collision map (tool-vs-wheel and each robot link vs wheel). If it flags now,
# the root cause is proven: the wheel is simply absent from the active map.
# Session-only change; pairs restored to COLLISION_OFF afterwards. No disk write.
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
print("wheel valid:", wheel.Valid(), " tool:", tool.Name())

saved = robot.Joints().list()[:6]
poseA = robomath.xyzrpw_2_pose([0, -762.7, 300, -90, 0, 180])     # face 1mm off rim
poseProbe = robomath.xyzrpw_2_pose([0, -780.0, 300, -90, 0, 180]) # face 16.4mm inside

def run_check(tag):
    prog = RDK.AddProgram("_probe_wheel_ctl", robot)
    try:
        prog.setVisible(False)
        prog.setPoseFrame(robot.PoseFrame())
        prog.setPoseTool(robot.PoseTool())
        robot.setJoints(saved)
        robot.MoveJ(poseA)
        prog.MoveJ(poseA)
        prog.MoveL(poseProbe)
        msg, mat, status = prog.InstructionListJoints(mm_step=1, deg_step=1, collision_check=robolink.COLLISION_ON)
        pairs = RDK.CollisionPairs()
        print("[%s] status=%s msg=%r pairs=%s" % (tag, status, (msg or "")[:120],
              [(a.Name(), b.Name()) for a, b, _, _ in pairs]))
    finally:
        prog.Delete()

# 1) tool vs wheel ON
r1 = RDK.setCollisionActivePair(robolink.COLLISION_ON, tool, wheel)
run_check("tool-wheel ON (r=%s)" % r1)

# 2) each robot link vs wheel ON
for link in range(1, 7):
    r = RDK.setCollisionActivePair(robolink.COLLISION_ON, robot, wheel, link, 0)
    print("link %s vs wheel -> %s" % (link, r))
run_check("robot links vs wheel ON")

# restore (behavioural baseline: pairs absent from map = OFF)
RDK.setCollisionActivePair(robolink.COLLISION_OFF, tool, wheel)
for link in range(1, 7):
    RDK.setCollisionActivePair(robolink.COLLISION_OFF, robot, wheel, link, 0)
robot.setJoints(saved)
print("restored joints:", [round(x, 3) for x in robot.Joints().list()[:6]])
print("done")
