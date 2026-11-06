#!/usr/bin/env python3
"""探针21：差分验证 AddCurve 黄曲线在 3D 视图中的可见性与颜色。
A = 曲线可见截图；B = 隐藏曲线截图；diff 像素即曲线本体，统计其色相。
"""
import os

from PIL import Image
from robodk.robolink import Robolink

RDK = Robolink()
curve = RDK.Item("_探针_黄曲线测试")
print("curve:", curve.Name() if curve.Valid() else "(invalid)")
if not curve.Valid():
    raise SystemExit("曲线对象不存在，先跑 trace_curve_probe20.py")

A = os.path.abspath("_probe21_A.png")
B = os.path.abspath("_probe21_B.png")
RDK.Command("Snapshot", A)
curve.setParam("Visible", "0")  # 隐藏
RDK.Command("Snapshot", B)
curve.setParam("Visible", "1")  # 恢复显示

ia, ib = Image.open(A).convert("RGB"), Image.open(B).convert("RGB")
w, h = ia.size
pa, pb = ia.load(), ib.load()
diff = [(x, y) for y in range(h) for x in range(w) if pa[x, y] != pb[x, y]]
print("size", w, h, "diff px", len(diff))
if diff:
    rs = [pa[x, y][0] for x, y in diff]
    gs = [pa[x, y][1] for x, y in diff]
    bs = [pa[x, y][2] for x, y in diff]
    n = len(diff)
    print("diff 区颜色均值 RGB=(%.0f, %.0f, %.0f)" % (sum(rs)/n, sum(gs)/n, sum(bs)/n))
    yellow = [p for p in diff if pa[p[0], p[1]][0] > 170 and pa[p[0], p[1]][1] > 120 and pa[p[0], p[1]][2] < 110]
    print("黄色系像素:", len(yellow), "/", n)
    xs = [p[0] for p in diff]; ys = [p[1] for p in diff]
    print("diff 范围 x %d..%d y %d..%d" % (min(xs), max(xs), min(ys), max(ys)))
    # 打几行代表性颜色
    seen = {}
    for x, y in diff:
        c = pa[x, y]
        seen[c] = seen.get(c, 0) + 1
    top = sorted(seen.items(), key=lambda kv: -kv[1])[:10]
    print("出现最多的颜色:", top)
