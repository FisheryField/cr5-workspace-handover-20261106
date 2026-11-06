#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Have the operator turn off the trace "References" display, and capture which
setting changed - so it can be applied programmatically afterwards.

The trace menu has: Trace on/off, Line / Points / Dots / Spheres, References,
Reset.  "References" draws a red/green/blue axis triad at every trace point,
which is exactly the "yellow curve with perpendicular red/green/blue segments"
the operator described.
"""
import filecmp
import json
import os
import shutil
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)
APPDATA = os.path.join(os.environ["APPDATA"], "RoboDK")
INI = os.path.join(APPDATA, "settings.ini")

RDK = Robolink()


def snapshot(tag):
    dst = os.path.join(OUT, "settings_%s.ini" % tag)
    shutil.copy2(INI, dst)
    params = {}
    try:
        for k, v in RDK.getParams():
            params[k] = v
    except Exception as e:  # noqa: BLE001
        params["_error"] = str(e)
    with open(os.path.join(OUT, "params_%s.json" % tag), "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=1, default=str)
    return dst, params


before_ini, before_params = snapshot("before_refoff")

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

messagebox.showinfo(
    "关闭 trace 的三色坐标轴（References）",
    "请在 RoboDK 顶部菜单里找到【Trace / 轨迹】菜单\n"
    "（通常和『显示』『工具』在同一排，图标是一条小曲线）。\n\n"
    "里面有一组可勾选项，类似：\n"
    "    Trace       (开关)\n"
    "    Line / Points / Dots / Spheres   (轨迹样式)\n"
    "    References  ← 把这个【取消勾选】\n"
    "    Reset\n\n"
    "取消勾选 References 之后，轨迹上那些垂直于曲线的红/绿/蓝小线段就会消失，\n"
    "只剩单色曲线。\n\n"
    "做完请按『确定』，我会自动把配置差异读出来。", parent=root)

after_ini, after_params = snapshot("after_refoff")

print("=== settings.ini changed? ===", not filecmp.cmp(before_ini, after_ini, shallow=False))
try:
    import configparser
    a = configparser.ConfigParser()
    b = configparser.ConfigParser()
    a.read(before_ini, encoding="utf-8")
    b.read(after_ini, encoding="utf-8")
    keys = set(a.defaults()) | set(b.defaults())
    for sec in set(a.sections()) | set(b.sections()):
        keys |= {k for k in a[sec]} | {k for k in b[sec]}
    for k in sorted(keys):
        va = b.get("General", k, fallback=None) or a.get("General", k, fallback=None)
        if va is None:
            va = ""
        vb = b.get("General", k, fallback=None) or a.get("General", k, fallback=None)
        if va != vb:
            print("   %-32s %r -> %r" % (k, va, vb))
except Exception as e:  # noqa: BLE001
    print("ini diff failed:", e)

print("\n=== param changes ===")
for k in sorted(set(before_params) | set(after_params)):
    if before_params.get(k) != after_params.get(k):
        print("   %-32s %r -> %r" % (k, before_params.get(k), after_params.get(k)))

print("\ncurrent Trace_Render_Style =", RDK.getParam("Trace_Render_Style"))
root.destroy()
