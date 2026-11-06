#!/usr/bin/env python3
"""探针29：确定 TCP 世界坐标的正确组合式。
比对：tool.PoseAbs()  vs  base*SolveFK(裸)*tool.PoseTool()
以及 SolveFK(q, tool_pose) 是否等于 SolveFK(裸)。
"""
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)

q0 = robot.Joints().list()[:6]
base_pose = robot.PoseAbs()
tool_pose = tool.PoseTool()

p_abs = tool.PoseAbs()
p_fk_with_tool = robot.SolveFK(q0, tool_pose)
p_fk_bare = robot.SolveFK(q0)

print("PoseAbs.Pos        :", [round(v, 2) for v in p_abs.Pos()])
print("SolveFK(带tool).Pos :", [round(v, 2) for v in p_fk_with_tool.Pos()])
print("SolveFK(裸).Pos     :", [round(v, 2) for v in p_fk_bare.Pos()])
p_comp = base_pose * p_fk_bare * tool_pose
print("base*FK*tool.Pos   :", [round(v, 2) for v in p_comp.Pos()])
print("组合式 vs PoseAbs 最大偏差 mm:",
      round(max(abs(a - b) for a, b in zip(p_abs.Pos(), p_comp.Pos())), 4))
