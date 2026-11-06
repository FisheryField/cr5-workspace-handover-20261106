#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the STATION-level trace parameters before/after the operator toggles the
trace "References" display, so the exact knob can be identified.

RoboDK keeps settings both globally (settings.ini, Robolink.getParam) and per
station (the .rdk / station item params, Item.setParam) - the station copy had
Trace_Render_Style = 2 while the global one was 0.
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
KEYS = ["Trace_Render_Style", "TraceStyle", "Trace", "Trace_References",
        "Trace_Render_References", "Show_Trace", "Trace_Active"]

RDK = Robolink()
station = RDK.ActiveStation()


def read_all(tag):
    out = {"global": {}, "station": {}}
    for k in KEYS:
        try:
            out["global"][k] = RDK.getParam(k)
        except Exception as e:  # noqa: BLE001
            out["global"][k] = "EXC:%s" % type(e).__name__
        try:
            out["station"][k] = station.getParam(k)
        except Exception as e:  # noqa: BLE001
            out["station"][k] = "EXC:%s" % type(e).__name__
    print("--- %s ---" % tag)
    for scope in ("global", "station"):
        for k, v in out[scope].items():
            if v is not None and not str(v).startswith("EXC"):
                print("   %-8s %-28s = %r" % (scope, k, v))
    return out


before = read_all("before")

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

messagebox.showinfo(
    "关闭轨迹上的红绿蓝小坐标轴",
    "请在 RoboDK 菜单栏里找到【Trace / 轨迹】菜单（图标像一条小曲线，\n"
    "通常跟『显示』『工具』在一排），里面是可勾选项：\n\n"
    "    Trace / Line / Points / Dots / Spheres / References / Reset\n\n"
    "请把【References】取消勾选（它让轨迹每点都画出 X/Y/Z 红绿蓝小轴）。\n\n"
    "如果菜单里没有 References，就点『确定』告诉我，我换别的方法。", parent=root)

done = messagebox.askyesno(
    "确认",
    "你成功取消勾选 References 了吗？\n\n"
    "是 = 已取消（轨迹上的红绿蓝小线段应该消失了）\n"
    "否 = 没找到 / 点了没反应", parent=root)
print("operator_says_done =", done)

after = read_all("after")

print("\n=== differences ===")
found = False
for scope in ("global", "station"):
    for k in KEYS:
        a, b = before[scope][k], after[scope][k]
        if a != b:
            found = True
            print("   %-8s %-28s %r -> %r" % (scope, k, a, b))
if not found:
    print("   none")

if done:
    ans = messagebox.askyesno(
        "效果确认",
        "现在轨迹上的红/绿/蓝小坐标轴线段【消失】了吗？\n\n"
        "是 = 搞定，我记录这个设置\n"
        "否 = 还在（我换别的方法）", parent=root)
    print("references_gone =", ans)

with open(os.path.join(OUT, "references_probe.json"), "w", encoding="utf-8") as f:
    json.dump({"before": before, "after": after, "done": bool(done)},
              f, ensure_ascii=False, indent=1, default=str)
root.destroy()
