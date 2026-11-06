#!/usr/bin/env python3
"""探针31：定位 FK 基准差异。查关节总数、父级链、各候选基座组合出的 TCP。"""
from robodk import robomath
from robodk.robolink import (Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL,
                             ITEM_TYPE_FRAME, ITEM_TYPE_STATION)

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)

jall = robot.Joints().list()
print("关节数 =", len(jall), "值 =", [round(v, 3) for v in jall])
print("robot.Parent() =", repr(robot.Parent().Name()))
st = robot.Parent()
gp = st.Parent()
print("station.Parent() =", repr(gp.Name()) if gp.Valid() else "(root)")

tool_pose = tool.PoseTool()
actual = tool.PoseAbs().Pos()
print("actual TCP:", [round(v, 2) for v in actual])

fk_bare = robot.SolveFK(jall[:6])
cands = {
    "robot.PoseAbs()": robot.PoseAbs(),
    "station.PoseAbs()": st.PoseAbs(),
}
try:
    fr = robot.getLink(ITEM_TYPE_FRAME)
    if fr.Valid():
        cands["link FRAME"] = fr.PoseAbs()
        print("frame item:", fr.Name())
except Exception as e:
    print("frame:", e)
if gp.Valid():
    cands["gp.PoseAbs()"] = gp.PoseAbs()

for name, base in cands.items():
    p = (base * fk_bare * tool_pose).Pos()
    dev = max(abs(a - b) for a, b in zip(actual, p))
    print("%-18s -> %s  偏差 %.3f mm" % (name, [round(v, 1) for v in p], dev))

# 关节全量 FK（若 >6 关节，外部轴可能有非零值）
if len(jall) > 6:
    fk_full = robot.SolveFK(jall)
    p = (robot.PoseAbs() * fk_full * tool_pose).Pos()
    print("全关节FK+base     -> %s  偏差 %.3f mm"
          % ([round(v, 1) for v in p], max(abs(a - b) for a, b in zip(actual, p))))
