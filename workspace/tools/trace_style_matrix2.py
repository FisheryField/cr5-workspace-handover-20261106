#!/usr/bin/env python3
"""探针19：用 setParam('Trace_Render_Style', n) 做样式矩阵（0..4）。
每档：设参数 -> On -> 运动 -> A -> Reset -> B -> 差分 -> 色调归类。
最后停在第 1 个 diff>0 且 yellow 占多数的档位（找不到则恢复 0）。"""
import colorsys
import os
import time
from collections import Counter

from PIL import Image
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]
A = os.path.abspath("_t19_A.png")
B = os.path.abspath("_t19_B.png")


def classify(diff):
    kinds = Counter()
    for _, _, (r, g, b) in diff:
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.25 and v > 0.6:
            kinds["white"] += 1
        elif 0.09 < hh < 0.19 and s > 0.4 and v > 0.4:
            kinds["yellow"] += 1
        elif hh < 0.05 or hh > 0.94:
            kinds["red"] += 1
        elif 0.25 < hh < 0.45:
            kinds["green"] += 1
        elif 0.55 < hh < 0.72:
            kinds["blue"] += 1
        else:
            kinds["other"] += 1
    return kinds


def one_round(tag):
    RDK.Command("Trace", "Off")
    RDK.Command("Trace", "Reset")
    RDK.Command("Trace", "On")
    q = saved_j[:]
    q[0] += 12
    robot.MoveJ(q)
    q[0] -= 12
    robot.MoveJ(q)
    time.sleep(0.4)
    RDK.Command("Snapshot", A)
    time.sleep(0.25)
    RDK.Command("Trace", "Reset")
    time.sleep(0.5)
    RDK.Command("Snapshot", B)
    ia = Image.open(A).convert("RGB")
    ib = Image.open(B).convert("RGB")
    pa, pb = ia.load(), ib.load()
    w, h = ia.size
    diff = []
    for y in range(h):
        for x in range(w):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            if abs(ra - rb) + abs(ga - gb) + abs(ba - bb) > 60:
                diff.append((x, y, (ra, ga, ba)))
    kinds = classify(diff)
    print(f"[{tag}] diffpx={len(diff):5d} kinds={dict(kinds)}")
    return diff, kinds


results = {}
for n in range(5):
    RDK.setParam("Trace_Render_Style", str(n))
    cur = RDK.getParam("Trace_Render_Style")
    diff, kinds = one_round(f"style={n} (read={cur})")
    results[n] = (len(diff), kinds)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("summary:", {n: (c, dict(k)) for n, (c, k) in results.items()})
