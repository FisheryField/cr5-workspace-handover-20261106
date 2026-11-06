#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decide Trace_Render_Style by eye: draw the same simulated path, then for each
candidate value ask the operator whether the trace is now a single yellow curve.

RunMode must be simulate (asserted) - the real robot is never commanded.
"""
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)

RDK = Robolink()
if RDK.RunMode() != 1:
    print("!! RunMode != simulate - ABORT")
    sys.exit(2)

robot = RDK.ItemList(2)[0]
print("robot:", robot.Name().encode("unicode_escape").decode("ascii"))
q0 = robot.Joints().list()[:6]

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

messagebox.showinfo(
    "轨迹样式测试 - 开始",
    "我会在 RoboDK 里用【仿真模式】画一段末端轨迹（不动真机），\n"
    "然后依次切换 4 种轨迹样式，每种都会问你一句：\n\n"
    "「现在这条轨迹是【单色黄色曲线】了吗？」\n\n"
    "请只回答这一句，答『是』我就停。", parent=root)


def draw(tag):
    RDK.Command("Trace", "Reset")
    RDK.Command("Trace", "On")
    robot.setSpeed(600)
    for k in range(15):
        a = k / 14.0
        q = list(q0)
        q[0] = q0[0] + 25.0 * a
        q[1] = q0[1] - 18.0 * a
        q[3] = q0[3] + 15.0 * a
        q[4] = q0[4] + 12.0 * a
        robot.MoveJ(q)
    robot.MoveJ(q0)
    RDK.Render(True)


result = {"tried": [], "best": None}
for style in (0, 1, 2, 3):
    RDK.setParam("Trace_Render_Style", style)
    draw(style)
    ok = messagebox.askyesno(
        "轨迹样式 %d/4" % (style + 1),
        "当前 Trace_Render_Style = %d\n\n"
        "现在那条末端轨迹是【单色的黄色曲线】了吗？\n\n"
        "是 = 就是这个，我停在这里\n"
        "否 = 继续试下一个" % style, parent=root)
    result["tried"].append({"style": style, "yellow_curve": bool(ok)})
    print("style %d -> yellow curve? %s" % (style, ok))
    if ok:
        result["best"] = style
        break

robot.MoveJ(q0)
RDK.Command("Trace", "Reset")
if result["best"] is None:
    RDK.setParam("Trace_Render_Style", 0)
print("RESULT: " + json.dumps(result))
with open(os.path.join(OUT, "style_dialog_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
root.destroy()
