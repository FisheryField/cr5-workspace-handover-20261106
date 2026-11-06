#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# read-only: settle TCP semantics. No moves.
import sys, io, inspect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

# 1) API semantics from source docstrings
src = inspect.getsource(robolink.Item.Pose)
print("=== Item.Pose docstring ===")
print("\n".join(src.splitlines()[:12]))
mv = inspect.getsource(robolink.Item.MoveJ)
print("=== Item.MoveJ docstring (head) ===")
print("\n".join(mv.splitlines()[:14]))

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
tool = robot.getLink(robolink.ITEM_TYPE_TOOL)
print("\nactive tool:", tool.Name())
print("PoseTool:\n", robot.PoseTool())

j = robot.Joints()
fk = robot.SolveFK(j)          # flange pose, authoritative
p_pose = robot.Pose()          # ?
print("\nSolveFK(joints) [flange]:\n", fk)
print("robot.Pose():\n", p_pose)
same = all(abs(fk[i][j_] - p_pose[i][j_]) < 0.01 for i in range(3) for j_ in (0, 3)) and \
       all(abs(fk[i][k] - p_pose[i][k]) < 0.001 for i in range(3) for k in (1, 2))
print("Pose() == SolveFK() ?", same, "-> Pose() is", "FLANGE" if same else "TOOL TCP")
if not same:
    tcp = fk * robot.PoseTool()
    tcp2 = p_pose * robot.PoseTool()
    print("fk*PoseTool:\n", tcp)
    print("Pose()*PoseTool:\n", tcp2)

# 2) what did walk-A joints actually give? (from recorded output)
walkA_j = [-73.707, -39.988, -104.379, 144.367, 73.707, 0.0]
fkA = robot.SolveIK  # noqa (keep reference)
from robodk.robomath import xyzrpw_2_pose, pose_2_xyzrpw
fkA_pose = robot.SolveFK(walkA_j)
print("\nwalk-A joints FK [flange]:", [round(v,2) for v in pose_2_xyzrpw(fkA_pose)])
print("walk-A joints FK * PoseTool (handle origin):", [round(v,2) for v in pose_2_xyzrpw(fkA_pose * robot.PoseTool())])
print("walk-A target was (0,-762.7,300,-90,0,180)")
