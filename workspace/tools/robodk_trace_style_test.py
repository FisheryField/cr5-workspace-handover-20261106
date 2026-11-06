#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find which Trace_Render_Style value renders RoboDK's default yellow trace.

Method: in SIMULATE mode only (asserted, aborting otherwise), draw the same
short joint path for each candidate style, snapshot the 3D view and count the
pixels by colour. The default yellow curve should maximise yellow and minimise
red/green/blue.

Safety: the RunMode must be 1 (simulate) or the script aborts before moving
anything; the robot is returned to its original joints at the end.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)
SIMULATE = 1

RDK = Robolink()
mode = RDK.RunMode()
print("RunMode =", mode)
if mode != SIMULATE:
    print("!! RunMode is not simulate - ABORT (no motion performed)")
    sys.exit(2)

robot = None
try:
    lst = RDK.ItemList(2)          # ITEM_TYPE_ROBOT
    for it in lst:
        print("robot candidate:", it.Name().encode("unicode_escape").decode("ascii"))
    if lst:
        robot = lst[0]
except Exception as e:  # noqa: BLE001
    print("ItemList EXC", e)

print("\n--- station tree ---")
def walk(item, depth=0):
    try:
        name = item.Name().encode("unicode_escape").decode("ascii")
    except Exception:  # noqa: BLE001
        name = "?"
    print("   " + "  " * depth + "%s (type %s)" % (name, item.Type()))
    for c in item.Childs():
        walk(c, depth + 1)

walk(RDK.ActiveStation())
if robot is None:
    print("!! no robot in the station")
    sys.exit(3)
print("robot:", robot.Name().encode("unicode_escape").decode("ascii"))

q0 = robot.Joints().list()[:6]
print("saved joints:", [round(v, 3) for v in q0])


def colours(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    yellow = ((r > 160) & (g > 160) & (b < 120) & (abs(r - g) < 60)).sum()
    return {
        "yellow": int(yellow),
        "red": int(((r - np.maximum(g, b) > 60) & (r > 110)).sum()),
        "green": int(((g - np.maximum(r, b) > 50) & (g > 100)).sum()),
        "blue": int(((b - np.maximum(r, g) > 50) & (b > 110)).sum()),
        "cyan": int(((g > 140) & (b > 140) & (r < 130)).sum()),
    }


def draw_path(tag):
    RDK.Command("Trace", "Reset")
    RDK.Command("Trace", "On")
    robot.setSpeed(500)
    # a small, smooth joint-space arc: 9 waypoints, back and forth
    for k in range(9):
        a = k / 8.0
        q = list(q0)
        q[0] = q0[0] + 12.0 * a
        q[1] = q0[1] - 8.0 * a
        q[4] = q0[4] + 6.0 * a
        robot.MoveJ(q)
    robot.MoveJ(q0)
    RDK.Render(True)
    p = os.path.join(OUT, "styletest_%s.png" % tag)
    RDK.Cam2D_Snapshot(p, None)
    return p, colours(p)


results = {}
for style in (0, 1, 2, 3):
    try:
        RDK.setParam("Trace_Render_Style", style)
    except Exception as e:  # noqa: BLE001
        print("setParam(%d) EXC %s" % (style, e))
    print("Trace_Render_Style =", RDK.getParam("Trace_Render_Style"))
    p, c = draw_path(style)
    results[style] = c
    print("   style %d -> %s" % (style, c))

robot.MoveJ(q0)
RDK.Command("Trace", "Reset")

print("\n=== summary (a yellow curve should have big yellow / small red+green+blue) ===")
print("%-6s %8s %8s %8s %8s %8s  %s" % ("style", "yellow", "red", "green", "blue", "cyan", "score(yellow-rgb)"))
best, best_score = None, -10 ** 9
for style, c in results.items():
    score = c["yellow"] - (c["red"] + c["green"] + c["blue"])
    print("%-6d %8d %8d %8d %8d %8d  %d" % (style, c["yellow"], c["red"], c["green"], c["blue"], c["cyan"], score))
    if score > best_score:
        best, best_score = style, score

print("\nbest style for 'default yellow curve' =", best)
RDK.setParam("Trace_Render_Style", best)
print("applied ->", RDK.getParam("Trace_Render_Style"))
with open(os.path.join(OUT, "style_test.json"), "w", encoding="utf-8") as f:
    json.dump({"results": results, "best": best, "joints_before": q0}, f, indent=1)
