#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Empirical probe (simulation only): does the collision map include the wheel?
# Plan: MoveJ sim to A pose (handle face 1mm off rim), build temp program with
# one MoveL that pushes 17.3mm deeper into the wheel, run the SAME check the
# script uses (InstructionListJoints, collision_check=COLLISION_ON), print status
# and the offending collision pairs by name. Then delete program, restore joints.
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink, robomath
from robodk.robolink import ITEM_TYPE_PROGRAM

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
st = robot.ConnectedState()
if (st[0] if isinstance(st, tuple) else st) not in (-2, -1, 0):
    print("ABORT: driver connected"); sys.exit(2)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

saved = robot.Joints().list()[:6]

# baseline pose A: TCP (0,-762.7,300,-90,0,180), handle +Z face at y=-775, rim y=-776
poseA = robomath.xyzrpw_2_pose([0, -762.7, 300, -90, 0, 180])
# probe: push 17.3mm deeper -> handle face y=-792.4, i.e. 16.4mm INSIDE the wheel
poseProbe = robomath.xyzrpw_2_pose([0, -780.0, 300, -90, 0, 180])

prog = RDK.AddProgram("_probe_wheel_collision", robot)
try:
    prog.setVisible(False)
    prog.setPoseFrame(robot.PoseFrame())
    prog.setPoseTool(robot.PoseTool())
    robot.setJoints(saved)
    robot.MoveJ(poseA)   # sim move to start
    prog.MoveJ(poseA)
    prog.MoveL(poseProbe)
    msg, mat, status = prog.InstructionListJoints(mm_step=1, deg_step=1, collision_check=robolink.COLLISION_ON)
    print("InstructionListJoints status =", status, "(<0 = collision/unreachable)")
    print("message head:", msg[:300] if msg else "(empty)")
    pairs = RDK.CollisionPairs()
    print("CollisionPairs (current offending pairs):")
    for a, b, ia, ib in pairs:
        print("   %s[link %s]  <->  %s[link %s]" % (a.Name(), ia, b.Name(), ib))
    if not pairs:
        print("   (none reported)")
finally:
    prog.Delete()
    robot.setJoints(saved)
print("restored joints:", [round(x,3) for x in robot.Joints().list()[:6]])
print("done")
