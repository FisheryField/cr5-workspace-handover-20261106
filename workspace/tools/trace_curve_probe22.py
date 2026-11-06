#!/usr/bin/env python3
"""探针22：判别「曲线不可见」还是「Visible 参数无效」。
方法：A 截图 -> 删除曲线 -> B 截图 -> 差分。删除是决定性的。
同时打印曲线的可见性参数、父级、边界盒。
"""
import os

from PIL import Image
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT

RDK = Robolink()
curve = RDK.Item("_探针_黄曲线测试")
print("curve:", curve.Name() if curve.Valid() else "(invalid)")
if not curve.Valid():
    raise SystemExit("曲线对象不存在")

try:
    print("Visible param:", repr(curve.getParam("Visible")))
except Exception as e:
    print("getParam Visible 失败:", e)
try:
    print("父级:", curve.Parent().Name())
except Exception as e:
    print("Parent 失败:", e)
try:
    print("边界盒:", curve.getBoundingBox())
except Exception as e:
    print("getBoundingBox 失败:", e)

A = os.path.abspath("_probe22_A.png")
B = os.path.abspath("_probe22_B.png")
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
    print("diff 区 A 侧颜色均值 RGB=(%.0f, %.0f, %.0f)" % (sum(rs)/n, sum(gs)/n, sum(bs)/n))
    xs = [p[0] for p in diff]; ys = [p[1] for p in diff]
    print("diff 范围 x %d..%d y %d..%d" % (min(xs), max(xs), min(ys), max(ys)))
