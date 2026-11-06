#!/usr/bin/env python3
"""探针16：只做 Command('Trace','Line')，On/Reset 差分 → 色调统计。
判定标准：diff 像素以黄色（R、G 高，B 低）为主 = Line 样式生效。"""
import colorsys
import os
import time
from collections import Counter

from PIL import Image
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]
a = os.path.abspath("_trace_cmdline_on.png")
b = os.path.abspath("_trace_cmdline_cleared.png")

RDK.Command("Trace", "Line")   # 唯一样式操作
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved_j[:]
q[0] += 12
robot.MoveJ(q)
q[0] -= 12
robot.MoveJ(q)
time.sleep(0.4)
RDK.Command("Snapshot", a)
time.sleep(0.3)
RDK.Command("Trace", "Reset")
time.sleep(0.5)
RDK.Command("Snapshot", b)

ia = Image.open(a).convert("RGB")
ib = Image.open(b).convert("RGB")
pa, pb = ia.load(), ib.load()
w, h = ia.size
diff = []
for y in range(h):
    for x in range(w):
        ra, ga, ba = pa[x, y]
        rb, gb, bb = pb[x, y]
        if abs(ra - rb) + abs(ga - gb) + abs(ba - bb) > 60:
            diff.append((x, y, (ra, ga, ba)))
print("diff px:", len(diff))
cnt = Counter(((r // 48 * 48, g // 48 * 48, b // 48 * 48) for _, _, (r, g, b) in diff))
for c, n in cnt.most_common(10):
    print(c, n)
# 色调归类
kinds = Counter()
for _, _, (r, g, b) in diff:
    hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.25 and v > 0.6:
        kinds["white"] += 1
    elif 0.09 < hh < 0.19 and s > 0.4 and v > 0.4:
        kinds["yellow"] += 1
    elif hh < 0.05 or hh > 0.94:
        kinds["red"] += 1
    elif 0.30 < hh < 0.70:
        kinds["green/blue"] += 1
    else:
        kinds["other"] += 1
print(kinds)
if diff:
    xs = [p[0] for p in diff]
    ys = [p[1] for p in diff]
    print("x:", min(xs), max(xs), "y:", min(ys), max(ys))
    print("samples:", diff[:6])
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
