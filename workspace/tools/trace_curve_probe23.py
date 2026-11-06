#!/usr/bin/env python3
"""探针23：正面判别 AddCurve 渲染路径。
建一条大跨度折线（x -800..800，跨度 1600mm，z=400）+ 一个大跨度彩色点集，
截图 A -> 删除 -> 截图 B -> 差分。差分>0 说明渲染路径 OK，是原曲线太小/被挡。
"""
import os

from PIL import Image
from robodk import robomath
from robodk.robolink import Robolink, PROJECTION_NONE

RDK = Robolink()

pts = []
for i in range(9):
    pts.append([-800.0 + 200.0 * i, 900.0, 400.0 + (150.0 if i % 2 else -150.0)])
mat = robomath.Mat([list(p) for p in pts]).tr()
curve = RDK.AddCurve(mat, None, False, PROJECTION_NONE)
curve.setName("_探针23_大折线")
curve.setColorCurve([1.0, 0.82, 0.0, 1.0])
print("curve:", curve.Name(), curve.Valid())

A = os.path.abspath("_probe23_A.png")
B = os.path.abspath("_probe23_B.png")
RDK.Command("Snapshot", A)
curve.Delete()
RDK.Command("Snapshot", B)

ia, ib = Image.open(A).convert("RGB"), Image.open(B).convert("RGB")
w, h = ia.size
pa, pb = ia.load(), ib.load()
diff = [(x, y) for y in range(h) for x in range(w) if pa[x, y] != pb[x, y]]
print("size", w, h, "diff px", len(diff))
if diff:
    n = len(diff)
    rs = [pa[x, y][0] for x, y in diff]
    gs = [pa[x, y][1] for x, y in diff]
    bs = [pa[x, y][2] for x, y in diff]
    print("A侧均值 RGB=(%.0f, %.0f, %.0f)" % (sum(rs)/n, sum(gs)/n, sum(bs)/n))
    xs = [p[0] for p in diff]; ys = [p[1] for p in diff]
    print("diff 范围 x %d..%d y %d..%d" % (min(xs), max(xs), min(ys), max(ys)))
    yellow = [p for p in diff if pa[p[0], p[1]][0] > 170 and pa[p[0], p[1]][1] > 120 and pa[p[0], p[1]][2] < 110]
    print("黄色系:", len(yellow), "/", n)
