#!/usr/bin/env python3
"""探针26：窗口已恢复，重测内置 Trace 的 Line 样式（此前结论在快照冻结期测得，无效）。
setParam Trace_Render_Style=4 -> Trace On -> MoveJ 摆动 -> 截图A；
Trace Reset -> 截图B；diff 中找黄色像素。
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
target = None
for h in rows:
    b = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(h, b, 256)
    if "RoboDK - 不受限制" in b.value:
        target = h
        break
if target is None:
    raise SystemExit("未找到 RoboDK 主窗口")
if user32.IsIconic(target):
    user32.ShowWindow(target, 9)
    time.sleep(1.5)
print("窗口 0x%X iconic=%s" % (target, bool(user32.IsIconic(target))))

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
RDK.Render(True)
print("style before:", RDK.getParam("Trace_Render_Style"))
RDK.setParam("Trace_Render_Style", "4")
print("style now   :", RDK.getParam("Trace_Render_Style"))

saved = robot.Joints().list()[:6]
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
RDK.Render(True)
for d in (8, -8, 8, -8):
    q = list(saved)
    q[0] += d
    robot.MoveJ(q)
    time.sleep(0.2)

A = os.path.abspath("_probe26_A.png")
RDK.Command("Snapshot", A)
RDK.Command("Trace", "Reset")
RDK.Render(True)
time.sleep(0.8)
B = os.path.abspath("_probe26_B.png")
RDK.Command("Snapshot", B)
RDK.Command("Trace", "Off")

ia, ib = Image.open(A).convert("RGB"), Image.open(B).convert("RGB")
w, h = ia.size
pa, pb = ia.load(), ib.load()
diff = [(x, y) for y in range(h) for x in range(w) if pa[x, y] != pb[x, y]]
print("size", w, h, "diff px", len(diff))
if diff:
    n = len(diff)
    yellow = [p for p in diff if pa[p[0], p[1]][0] > 170 and pa[p[0], p[1]][1] > 120 and pa[p[0], p[1]][2] < 110]
    rs = [pa[x, y][0] for x, y in diff]
    gs = [pa[x, y][1] for x, y in diff]
    bs = [pa[x, y][2] for x, y in diff]
    print("A侧均值 RGB=(%.0f, %.0f, %.0f)" % (sum(rs)/n, sum(gs)/n, sum(bs)/n))
    print("黄色系:", len(yellow), "/", n)
    xs = [p[0] for p in diff]; ys = [p[1] for p in diff]
    print("范围 x %d..%d y %d..%d" % (min(xs), max(xs), min(ys), max(ys)))
robot.setJoints(saved)
RDK.setParam("Trace_Render_Style", "0")
print("关节复原:", [round(v, 2) for v in robot.Joints().list()[:6]], "style 还原为 0")
