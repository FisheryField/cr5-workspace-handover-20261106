#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive: make the TCP trajectory yellow, then ask the operator to confirm.

The 3D view cannot be inspected from the text side, so the operator answers a
couple of yes/no dialogs.

Steps
  1. record item visibility + colours (so everything is reversible)
  2. recolour every TCP* point item to yellow (setColor + setColorCurve)
  3. ask: is the end-effector trajectory yellow now?
  4. if not, hide all point/program items and ask whether the red/green/blue
     trajectory disappeared (identifies the source), then restore visibility
"""
import io
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)
YELLOW = [1.0, 1.0, 0.0, 1.0]

RDK = Robolink()
station = RDK.ActiveStation()

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)


def ask(title, question):
    return messagebox.askyesno(title, question, parent=root)


def note(title, text):
    messagebox.showinfo(title, text, parent=root)


answers = {}

items = []
for it in station.Childs():
    t = it.Type()
    if t in (7, 9, 10):          # Program / Curve / Points
        try:
            vis = int(it.Visible())
        except Exception:  # noqa: BLE001
            vis = 1
        col = None
        if t in (9, 10):
            try:
                col = list(it.Color())
            except Exception:  # noqa: BLE001
                col = None
        items.append({"item": it, "name": it.Name(), "type": t,
                      "visible": vis, "color": col})

with io.open(os.path.join(OUT, "items_state_before.json"), "w",
             encoding="utf-8") as f:
    json.dump([{k: v for k, v in d.items() if k != "item"} for d in items],
              f, ensure_ascii=False, indent=1)

note("RoboDK 轨迹颜色 - 开始",
     "接下来会有 2~3 个问题，请看着 RoboDK 的 3D 视图回答。\n\n"
     "第一步：把所有 TCP 轨迹点云改成黄色。")

changed = []
for d in items:
    if d["type"] != 10 or not d["name"].upper().startswith("TCP"):
        continue
    it = d["item"]
    try:
        it.setColor(YELLOW)
        changed.append(d["name"])
    except Exception as e:  # noqa: BLE001
        print("setColor EXC", d["name"].encode("unicode_escape").decode(), e)
    for fn in ("setColorCurve",):
        try:
            getattr(it, fn)(YELLOW)
        except Exception as e:  # noqa: BLE001
            print("%s EXC %s %s" % (fn, d["name"].encode("unicode_escape").decode(), e))

RDK.Render(True)
print("recoloured %d items to yellow" % len(changed))

answers["yellow_now"] = ask(
    "问题 1/2",
    "现在 3D 视图里那条「机器人末端运动轨迹」是【黄色】了吗？\n\n"
    "是 = 已经变黄（成功）\n"
    "否 = 还是红绿蓝交杂 / 或没变化")

if not answers["yellow_now"]:
    note("下一步",
         "我会把站里所有【点云/程序】对象临时隐藏，请再看一眼 3D 视图。")
    hidden = []
    for d in items:
        try:
            d["item"].setVisible(False)
            hidden.append(d["name"])
        except Exception:  # noqa: BLE001
            pass
    RDK.Render(True)
    answers["gone_when_hidden"] = ask(
        "问题 2/2",
        "那条红绿蓝交杂的末端轨迹现在【消失】了吗？\n\n"
        "是 = 它来自站里的点云/程序对象\n"
        "否 = 它来自别的东西（我会另找）")
    for d in items:
        try:
            d["item"].setVisible(d["visible"])
        except Exception:  # noqa: BLE001
            pass
    RDK.Render(True)

answers["changed_items"] = changed
with io.open(os.path.join(OUT, "operator_answers.json"), "w",
             encoding="utf-8") as f:
    json.dump(answers, f, ensure_ascii=False, indent=1)
print("ANSWERS: " + json.dumps(answers, ensure_ascii=False))
root.destroy()
