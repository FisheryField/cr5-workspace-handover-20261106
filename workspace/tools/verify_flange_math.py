#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only validation of the flange<->TCP maths used by 机械臂法兰真实运动.py.

Never commands motion: only SolveFK / SolveIK / Pose / PoseTool / PoseFrame.
Checks
  1. hub: does 'eye' exist in robomath (used as the identity tool fallback)
  2. flange via invH(PoseFrame)*SolveFK(Joints)  ==  Pose()*invH(PoseTool())
  3. TCP = flange*tool  ->  SolveIK(tcp, tool, frame) reproduces the current joints
  4. flange            ->  SolveIK(flange, reference=frame)  (tool-free form) does too
"""
import os
import sys

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import *          # noqa: E402,F403
from robodk import robomath            # noqa: E402
from robodk.robomath import Pose_2_Fanuc  # noqa: E402

print("robomath has eye():", hasattr(robomath, "eye"))
if hasattr(robomath, "eye"):
    print("eye(4) =", robomath.eye(4).tolist())

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
print("robot:", robot.Name().encode("unicode_escape").decode("ascii"), " valid:", robot.Valid())

frame = robot.PoseFrame()
tool = robot.PoseTool()
q = robot.Joints()


def fanuc(m):
    vals = Pose_2_Fanuc(m)
    vals = list(vals) if not isinstance(vals, list) else vals
    return [round(float(v), 4) for v in vals[:6]]


print("\nFrame     :", fanuc(frame))
print("Tool(PoseTool):", fanuc(tool))
print("Joints    :", [round(v, 3) for v in q.list()[:6]])


fl_a = robomath.invH(frame) * robot.SolveFK(q)          # tool-free flange
tcp = robot.Pose()                                       # TCP (active tool)
fl_b = tcp * robomath.invH(tool)                         # TCP * inv(tool)
print("\n1) flange from SolveFK :", fanuc(fl_a))
print("   flange from Pose/tool:", fanuc(fl_b))
d = max(abs(a - b) for a, b in zip(fanuc(fl_a), fanuc(fl_b)))
print("   max difference = %.6f  ->  %s" % (d, "MATCH" if d < 1e-6 else "MISMATCH"))

tcp_from_flange = fl_a * tool
q1 = robot.SolveIK(tcp_from_flange, tool=tool, reference=frame).list()
print("\n2) SolveIK(flange*tool, tool, frame) ->", [round(v, 3) for v in q1[:6]])
print("   max |dq| vs current joints = %.4f deg"
      % max(abs(a - b) for a, b in zip(q1[:6], q.list()[:6])))

q2 = robot.SolveIK(fl_a, reference=frame).list()
print("\n3) SolveIK(flange, reference=frame)  ->", [round(v, 3) for v in q2[:6]])
print("   max |dq| vs current joints = %.4f deg"
      % max(abs(a - b) for a, b in zip(q2[:6], q.list()[:6])))

is_identity = all(abs(a - b) < 1e-9 for a, b in
                  zip([v for v in tool.list()], [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]))
print("\ntool is identity:", is_identity,
      "(if True the flange and TCP scripts behave identically until a real tool is set)")
