#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ask the operator to click the mystery trajectory, then read what RoboDK
selected - that identifies exactly which item (or the robot/program) draws it.
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
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

messagebox.showinfo(
    "识别末端轨迹 - 步骤 1/2",
    "请在 RoboDK 的 3D 视图里用鼠标【点一下那条红绿蓝交杂的末端运动轨迹】。\n\n"
    "（点中时它会高亮；如果点不中，就点它附近的机器人或轨迹本身都可以）\n\n"
    "点完后再按下面的『确定』。", parent=root)

def selection():
    for name in ("Selection", "getSelectedItems", "SelectedItems"):
        try:
            fn = getattr(RDK, name)
            s = fn()
            return name, s
        except Exception:  # noqa: BLE001
            continue
    return None, []

api, sel = selection()
info = {"api": api, "selected": []}
for it in sel if isinstance(sel, (list, tuple)) else [sel]:
    try:
        d = {"name": it.Name(), "type": it.Type()}
        try:
            p = it.Parent()
            d["parent"] = p.Name() if p is not None and p.Valid() else None
        except Exception:  # noqa: BLE001
            d["parent"] = None
        try:
            d["visible"] = bool(it.Visible())
        except Exception:  # noqa: BLE001
            pass
        try:
            d["pose"] = [round(v, 1) for v in it.Pose().Pos().list()]
        except Exception:  # noqa: BLE001
            pass
        info["selected"].append(d)
    except Exception as e:  # noqa: BLE001
        info["selected"].append({"error": str(e)})

print("SELECTION_API:", api)
print("SELECTION:", json.dumps(info, ensure_ascii=False))
with open(os.path.join(OUT, "selected_item.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=1)

# second question: does clearing the built-in trace remove it?
messagebox.showinfo(
    "识别末端轨迹 - 步骤 2/2",
    "下一步我会执行 RoboDK 的 Trace Reset（清除内建轨迹显示）。\n"
    "请再看一眼 3D 视图，然后回答下面的问题。", parent=root)
try:
    print("Trace Reset ->", RDK.Command("Trace", "Reset"))
except Exception as e:  # noqa: BLE001
    print("Trace Reset EXC", e)
RDK.Render(True)

ans = messagebox.askyesno(
    "问题",
    "执行 Trace Reset 之后，那条红绿蓝交杂的末端轨迹【消失】了吗？\n\n"
    "是 = 它就是 RoboDK 内建 Trace（我知道怎么恢复成默认黄色曲线）\n"
    "否 = 不是内建 Trace（我会按你刚才点中的对象继续查）", parent=root)
print("GONE_AFTER_TRACE_RESET:", ans)
with open(os.path.join(OUT, "selected_item.json"), "a", encoding="utf-8") as f:
    f.write("\ngone_after_trace_reset=%s\n" % ans)
root.destroy()
