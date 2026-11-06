#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读查询 RoboDK 工作站：门把手_bs1 / 磨砂圆柱 / Dobot CR5 / P1 的位姿与参数。
绝对不做：连接/断开机器人、任何运动指令、任何 setXxx 修改。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from robodk import robolink

RDK = robolink.Robolink(robodk_ip='localhost')
print("RDK link established")

# 枚举全部对象（只读）
print("== 全部对象（类型/名称）==")
for it in RDK.ItemList():
    print("  type=%s  name=%s" % (it[1] if isinstance(it, tuple) else '?', it[0] if isinstance(it, tuple) else it))

def pose_of(name_kw):
    try:
        item = RDK.Item(name_kw, robolink.ITEM_TYPE_OBJECT)
        if item.Valid():
            p = item.getLink(robolink.ITEM_TYPE_ROBOT)
            print("[%s] pose: %s" % (name_kw, item.Pose()))
            return item.Pose()
    except Exception as e:
        print("[%s] err: %s" % (name_kw, e))
    return None

for nm in ["门把手_bs1", "磨砂圆柱", "Dobot CR5", "P1"]:
    pose_of(nm)
