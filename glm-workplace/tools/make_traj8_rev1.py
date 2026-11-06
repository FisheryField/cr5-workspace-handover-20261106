#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Build rev1 of 连续轨迹8: manually insert the script's own 3-step
# retreat-turn pattern between P10 and P11 (P11 flip was bare-connected).
# Original JSON on disk is NOT touched.
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹8.json"
DST = r"D:\mydata\glm-workplace\sim_scripts\连续轨迹8_rev1.json"

data = json.load(open(SRC, encoding="utf-8"))
assert len(data) == 12, "unexpected source shape"
p10 = data[9]   # (0, -762, 300, 180, 0, 180)
p11 = data[10]  # (30, -750, 300, -90, 0, -90)
assert p10["values"] == [0.0, -762.0, 300.0, 180.0, 0.0, 180.0], p10["values"]
assert p11["values"] == [30.0, -750.0, 300.0, -90.0, 0.0, -90.0], p11["values"]

retreat = {"type": "TCP", "values": [0.0, -750.0, 300.0] + p10["values"][3:], "singular": False, "j6_delta": 0}
turn    = {"type": "TCP", "values": [0.0, -750.0, 300.0] + p11["values"][3:], "singular": False, "j6_delta": 0}

out = data[:10] + [retreat, turn] + data[10:]
json.dump(out, open(DST, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("wrote", DST, "with", len(out), "points:")
for i, r in enumerate(out, 1):
    tag = "  <-- inserted" if r in (retreat, turn) else ""
    print("  P%-2d %s %s%s" % (i, r["type"], r["values"], tag))
