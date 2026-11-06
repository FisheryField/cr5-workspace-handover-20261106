#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
j_now = [round(x, 3) for x in robot.Joints().list()]
j0 = json.load(open(r"D:\mydata\glm-workplace\data\scripts_ref\sim_walk_j0.json", encoding="utf-8"))
j0r = [round(x, 3) for x in j0]
print("now :", j_now)
print("j0  :", j0r)
print("delta:", [round(a - b, 4) for a, b in zip(j_now, j0r)])
print("exactly home:", all(abs(a - b) < 0.01 for a, b in zip(j_now, j0r)))
print("ConnectedState:", robot.ConnectedState())
# 站内是否有活动 program（只读）
n = 0
for it in RDK.ItemList():
    t = it.type if hasattr(it, "type") else None
    n += 1
print("items:", n)
