#!/usr/bin/env python3
"""探针24：判别快照管线是否还活着。
① 基线截图 -> 关节动 10° -> 截图：diff 应 >0（相机活着、能拍到机器人）
② 建大曲线 + Render(True) + 延时 -> 截图A；删除 + 延时 -> 截图B：看曲线差分
③ 打印 ItemList 类型清单（确认 type-19 身份与站点数）
"""
import os
import time

from PIL import Image
from robodk import robomath
from robodk.robolink import Robolink, PROJECTION_NONE, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
RDK.Render(True)


def snap(name):
    p = os.path.abspath(name)
    RDK.Command("Snapshot", p)
    return Image.open(p).convert("RGB")


def diffpx(ia, ib):
    w, h = ia.size
    pa, pb = ia.load(), ib.load()
    return sum(1 for y in range(h) for x in range(w) if pa[x, y] != pb[x, y])


s0 = snap("_probe24_s0.png")
saved = robot.Joints().list()[:6]
q = list(saved)
q[0] += 10.0
robot.MoveJ(q)
time.sleep(0.3)
s1 = snap("_probe24_s1.png")
print("① 关节+10° 后 diff px =", diffpx(s0, s1))
robot.MoveJ(saved)
time.sleep(0.3)

pts = [[-800.0 + 200.0 * i, 900.0, 400.0 + (150.0 if i % 2 else -150.0)] for i in range(9)]
curve = RDK.AddCurve(robomath.Mat(pts).tr(), None, False, PROJECTION_NONE)
curve.setName("_探针24_大折线")
curve.setColorCurve([1.0, 0.82, 0.0, 1.0])
RDK.Render(True)
time.sleep(1.0)
sA = snap("_probe24_A.png")
curve.Delete()
RDK.Render(True)
time.sleep(1.0)
sB = snap("_probe24_B.png")
print("② 曲线建/删 diff px =", diffpx(sA, sB))

names = RDK.ItemList()
print("③ item 数 =", len(names))
import robodk.robolink as rl
for n in names:
    it = RDK.Item(n)
    print("   ", repr(n), "type", it.type if hasattr(it, "type") else "?", "id", it.id())
