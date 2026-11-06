#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix attempt: shrink/remove the coordinate systems RoboDK draws along paths
(the red/green/blue axis triads on the trace) with the FrameSizesPath command.

Sequence: draw a simulated path (so a trace exists) -> ask what is visible ->
set FrameSizesPath = 0 -> ask again. Simulation only (RunMode asserted).
"""
import json
import os
import sys
import tkinter as tk

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)

RDK = Robolink()
if RDK.RunMode() != 1:
    print("!! RunMode != simulate - ABORT")
    sys.exit(2)

robot = RDK.ItemList(2)[0]
q0 = robot.Joints().list()[:6]

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

CHOICES = ["只有单色曲线", "曲线+红绿蓝小坐标轴", "看不到轨迹", "其它"]


def ask_choice(title, question):
    win = tk.Toplevel(root)
    win.title(title)
    win.attributes("-topmost", True)
    win.geometry("+250+250")
    tk.Label(win, text=question, justify="left", padx=18, pady=14,
             font=("Microsoft YaHei", 11)).pack()
    res = {"v": None}

    def pick(v):
        res["v"] = v
        win.destroy()

    row = tk.Frame(win)
    row.pack(pady=10)
    for c in CHOICES:
        tk.Button(row, text=c, width=18, command=lambda c=c: pick(c)).pack(side=tk.LEFT, padx=4)
    win.wait_window()
    return res["v"]


def draw():
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


print("FrameSizesPath now =", RDK.Command("FrameSizesPath"))
print("FrameSizes now     =", RDK.Command("FrameSizes"))

draw()
a1 = ask_choice("步骤 1/2：当前状态",
                "我已经重新画了一条末端轨迹。\n\n现在它是什么样子？")
print("state1 =", a1)

print("set FrameSizesPath 0 ->", RDK.Command("FrameSizesPath", "0"))
RDK.Render(True)
a2 = ask_choice("步骤 2/2：FrameSizesPath = 0",
                "现在（FrameSizesPath = 0）轨迹是什么样子？")

res = {"state_before": a1, "state_after_framesizespath_0": a2,
       "framesizespath_was": str(RDK.Command("FrameSizesPath"))}
print("RESULT: " + json.dumps(res, ensure_ascii=False))
with open(os.path.join(OUT, "framesizespath_result.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

# leave the trace visible for the operator
draw()
root.destroy()
