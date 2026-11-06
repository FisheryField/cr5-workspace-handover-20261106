#!/usr/bin/env python3
"""探针32：工具父级链 + 精确差变换 X（X*fk*tool = actual）。"""
from robodk import robomath
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)

print("== 工具父级链 ==")
node = tool
depth = 0
while node.Valid() and depth < 8:
    pa = node.PoseAbs()
    print("  " * depth + "- %s  PoseAbs.Pos=%s" % (repr(node.Name()), [round(v, 1) for v in pa.Pos()]))
    node = node.Parent()
    depth += 1

q = robot.Joints().list()[:6]
fk = robot.SolveFK(q)
tp = tool.PoseTool()
actual = tool.PoseAbs()
X = actual * robomath.invH(fk * tp)
print("\nX = actual*inv(fk*tool):")
print(X.ApproxString() if hasattr(X, "ApproxString") else X)
print("X.Pos =", [round(v, 2) for v in X.Pos()])
rpy = robomath.pose_2_xyzrpw(X)[3:]
print("X rpy(deg) =", [round(v, 2) for v in rpy])

rb = robot.PoseAbs()
D = X * robomath.invH(rb)
print("D = X*inv(robot.PoseAbs): Pos =", [round(v, 2) for v in D.Pos()],
      " rpy =", [round(v, 2) for v in robomath.pose_2_xyzrpw(D)[3:]])
