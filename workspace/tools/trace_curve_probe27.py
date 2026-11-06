#!/usr/bin/env python3
"""探针27：管线正常后，实测三种设置 Trace 样式的方式到底渲染成什么。
A) setParam Trace_Render_Style=0 + Trace On
B) setParam Trace_Render_Style=4 + Trace On
C) Command('Trace','Line') + Trace On
每轮：摆动 J1 ±8° -> 截图 -> Trace Reset -> 截图 -> 差分统计（px 数 / 均值 / top 色）。
"""
import ctypes
import os
import time

import ctypes.wintypes as wt
from PIL import Image
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

user32 = ctypes.windll.user32
rows = []
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def cb(h, l):
    rows.append(h)
    return True


user32.EnumWindows(WNDENUMPROC(cb), 0)
for h in rows:
    b = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(h, b, 256)
    if "RoboDK - 不受限制" in b.value and user32.IsIconic(h):
        user32.ShowWindow(h, 9)
        time.sleep(1.0)
print("窗口已确认非最小化")

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
RDK.Render(True)
saved = robot.Joints().list()[:6]


def snap(name):
    p = os.path.abspath(name)
    RDK.Command("Snapshot", p)
    return Image.open(p).convert("RGB")


def one_round(tag, setup):
    RDK.Command("Trace", "Off")
    RDK.Command("Trace", "Reset")
    setup()
    RDK.Command("Trace", "On")
    RDK.Render(True)
    for d in (8, -8, 8, -8):
        q = list(saved)
        q[0] += d
        robot.MoveJ(q)
        time.sleep(0.15)
    ia = snap("_probe27_%s_A.png" % tag)
    RDK.Command("Trace", "Reset")
    RDK.Render(True)
    time.sleep(0.6)
    ib = snap("_probe27_%s_B.png" % tag)
    RDK.Command("Trace", "Off")
    w, h = ia.size
    pa, pb = ia.load(), ib.load()
    diff = [(x, y) for y in range(h) for x in range(w) if pa[x, y] != pb[x, y]]
    n = len(diff)
    if not n:
        print("[%s] diff px = 0" % tag)
        return
    rs = sum(pa[x, y][0] for x, y in diff) / n
    gs = sum(pa[x, y][1] for x, y in diff) / n
    bs = sum(pa[x, y][2] for x, y in diff) / n
    cnt = {}
    for x, y in diff:
        c = pa[x, y]
        cnt[c] = cnt.get(c, 0) + 1
    top = sorted(cnt.items(), key=lambda kv: -kv[1])[:6]
    yellow = sum(1 for x, y in diff if pa[x, y][0] > 170 and pa[x, y][1] > 120 and pa[x, y][2] < 110)
    print("[%s] diff px=%d 均值RGB=(%.0f,%.0f,%.0f) 黄=%d top色=%s" % (tag, n, rs, gs, bs, yellow, top))


one_round("A_param0", lambda: RDK.setParam("Trace_Render_Style", "0"))
one_round("B_param4", lambda: RDK.setParam("Trace_Render_Style", "4"))
one_round("C_cmdLine", lambda: (RDK.Command("Trace", "Line"), RDK.setParam("Trace_Render_Style", "0")))

RDK.setParam("Trace_Render_Style", "0")
robot.setJoints(saved)
print("收尾: style=0, 关节", [round(v, 2) for v in robot.Joints().list()[:6]])
