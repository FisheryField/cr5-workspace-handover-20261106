#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare two ways of drawing the simulated TCP path and let the operator say
which one is "RoboDK's default yellow curve":

  A) RoboDK's native trace        (RDK.Command('Trace','On'))
  B) an explicit YELLOW spray trace (RDK.Spray_Add(..., COLOR=yellow), SPRAY_ON)

Background (from Library/Macros/SpindleOn.py): every SpindleOn(n) call ADDS a
spray trace in COLOR_LIST[n] (0 white, 1 red, 2 green, 3 blue ...), so repeated
calls leave several differently coloured traces stacked - which matches the
"red/green/blue mixed" the operator reported.  Native trace is single colour.

Simulation only: RunMode must be 1, asserted before any motion.
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
print("robot OK, joints saved")

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

CHOICES = ["单色黄色", "红绿蓝交杂", "别的单色", "看不到"]


def ask_choice(title, question):
    win = tk.Toplevel(root)
    win.title(title)
    win.attributes("-topmost", True)
    win.geometry("+200+200")
    tk.Label(win, text=question, justify="left", padx=18, pady=14,
             font=("Microsoft YaHei", 11)).pack()
    result = {"v": None}

    def pick(v):
        result["v"] = v
        win.destroy()

    frm = tk.Frame(win)
    frm.pack(pady=10)
    for c in CHOICES:
        tk.Button(frm, text=c, width=12, command=lambda c=c: pick(c)).pack(side=tk.LEFT, padx=4)
    win.wait_window()
    return result["v"]


def clear_all():
    try:
        RDK.Spray_SetState(1)   # SPRAY_OFF = 1? try known constant names below
    except Exception:  # noqa: BLE001
        pass
    try:
        from robodk.robolink import SPRAY_OFF
        RDK.Spray_SetState(SPRAY_OFF)
    except Exception:  # noqa: BLE001
        pass
    RDK.Command("Trace", "Reset")


def draw(tag, way):
    clear_all()
    if way == "native":
        RDK.Command("Trace", "On")
    else:
        try:
            RDK.Spray_Add(0, 0, "PARTICLE=SPHERE(1.5,8) NO_PROJECT COLOR=yellow")
            from robodk.robolink import SPRAY_ON
            RDK.Spray_SetState(SPRAY_ON)
        except Exception as e:  # noqa: BLE001
            print("Spray_Add EXC", e)
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


answers = {}
draw("native", "native")
answers["A_native_trace"] = ask_choice(
    "实验 A：RoboDK 原生 trace",
    "现在这条末端轨迹是【什么样子】？")

if answers["A_native_trace"] != "单色黄色":
    draw("yellow", "spray")
    answers["B_yellow_spray"] = ask_choice(
        "实验 B：显式黄色喷迹（radius 1.5mm）",
        "现在这条末端轨迹是【什么样子】？")

print("ANSWERS: " + json.dumps(answers, ensure_ascii=False))
with open(os.path.join(OUT, "trace_ab_result.json"), "w", encoding="utf-8") as f:
    json.dump(answers, f, ensure_ascii=False, indent=1)
root.destroy()
