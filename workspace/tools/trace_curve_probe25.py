import ctypes
import os
import time

import ctypes.wintypes as wt
from PIL import Image
from robodk import robomath
from robodk.robolink import Robolink, PROJECTION_NONE

user32 = ctypes.windll.user32
h = 0x50AF2
if not user32.IsWindow(h):
    raise SystemExit("窗口句柄失效，需重新枚举")
print("iconic before:", bool(user32.IsIconic(h)))
user32.ShowWindow(h, 9)  # SW_RESTORE
time.sleep(1.5)
print("iconic after :", bool(user32.IsIconic(h)), "visible:", bool(user32.IsWindowVisible(h)))

RDK = Robolink()
RDK.Render(True)


def snap(name):
    p = os.path.abspath(name)
    RDK.Command("Snapshot", p)
    return Image.open(p).convert("RGB")


def diffpx(ia, ib):
    w, h = ia.size
    pa, pb = ia.load(), ib.load()
    return sum(1 for y in range(h) for x in range(w) if pa[x, y] != pb[x, y])


s0 = snap("_probe25_s0.png")
time.sleep(0.5)
s1 = snap("_probe25_s1.png")
print("静止双拍 diff =", diffpx(s0, s1), "（>0 说明渲染活跃有噪声，=0 说明静帧）")

pts = [[-800.0 + 200.0 * i, 900.0, 400.0 + (150.0 if i % 2 else -150.0)] for i in range(9)]
curve = RDK.AddCurve(robomath.Mat(pts).tr(), None, False, PROJECTION_NONE)
curve.setName("_probe25_大折线")
curve.setColorCurve([1.0, 0.82, 0.0, 1.0])
time.sleep(1.0)
sA = snap("_probe25_A.png")
curve.Delete()
time.sleep(1.0)
sB = snap("_probe25_B.png")
d = diffpx(sA, sB)
print("曲线建/删 diff px =", d)
if d:
    w, h = sA.size
    pa = sA.load()
    diff = [(x, y) for y in range(h) for x in range(w) if pa[x, y] != sB.load()[x, y]]
    n = len(diff)
    rs = [pa[x, y][0] for x, y in diff]
    gs = [pa[x, y][1] for x, y in diff]
    bs = [pa[x, y][2] for x, y in diff]
    print("A侧均值 RGB=(%.0f, %.0f, %.0f)" % (sum(rs)/n, sum(gs)/n, sum(bs)/n))
    xs = [p[0] for p in diff]; ys = [p[1] for p in diff]
    print("范围 x %d..%d y %d..%d" % (min(xs), max(xs), min(ys), max(ys)))
    yellow = [p for p in diff if pa[p[0], p[1]][0] > 170 and pa[p[0], p[1]][1] > 120 and pa[p[0], p[1]][2] < 110]
    print("黄色系:", len(yellow), "/", n)
