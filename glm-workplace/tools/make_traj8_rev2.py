#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Build rev2: retreat P10->(0,-750,180,0,180), then DIRECT MoveJ to original
# P11 (30,-750,-90,0,-90). The in-place turn is a proven geometric dead end
# (36/36 IK-pair bridges fail: wheel sweep / table / dev>500), while the direct
# bridge has 4 collision-free pairs at 421-427mm deviation (< 500 cap).
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹8.json"
DST = r"D:\mydata\glm-workplace\sim_scripts\连续轨迹8_rev2.json"

data = json.load(open(SRC, encoding="utf-8"))
assert len(data) == 12
p10, p11 = data[9], data[10]
assert p10["values"] == [0.0, -762.0, 300.0, 180.0, 0.0, 180.0]
assert p11["values"] == [30.0, -750.0, 300.0, -90.0, 0.0, -90.0]

retreat = {"type": "TCP", "values": [0.0, -750.0, 300.0] + p10["values"][3:], "singular": False, "j6_delta": 0}
out = data[:10] + [retreat] + data[10:]
json.dump(out, open(DST, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("wrote", DST, "with", len(out), "points:")
for i, r in enumerate(out, 1):
    tag = "  <-- inserted retreat" if r is retreat else ""
    print("  P%-2d %s%s" % (i, r["values"], tag))
