#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 生成修复后的 连续轨迹10_修复版.json（C 方案：接缝斜线拆两段，插 2 个高点平移）。
# 只写到本工作区 sim_scripts\，不动用户原始 JSON。
import json, copy
BASE = r"D:\mydata\working things\dobot_arm\RoboDK files 2"
src = json.load(open(BASE + r"\连续轨迹10.json", encoding="utf-8"))
def tcp(v, sing=False, spin=False, d=0):
    return {"type": "TCP", "values": [float(x) for x in v],
            "singular": sing, "spin360": spin, "j6_delta": d}
out = []
inserted = 0
for i, p in enumerate(src):
    # 接缝斜线：从 P12 (0,-462,400,90,0,90) 指向 P13 (40,-750,300,90,0,90)
    if (p["type"] == "TCP" and [round(float(x), 3) for x in p["values"]] == [40.0, -750.0, 300.0, 90.0, 0.0, 90.0]
            and inserted == 0):
        out.append(tcp([40, -462, 400, 90, 0, 90]))
        out.append(tcp([40, -750, 400, 90, 0, 90]))
        inserted += 1
    out.append(copy.deepcopy(p))
dst = r"D:\mydata\glm-workplace\sim_scripts\连续轨迹10_修复版.json"
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("原始 %d 点 -> 修复版 %d 点（插入 %d 个高点）" % (len(src), len(out), inserted))
for i, p in enumerate(out):
    v = p["values"]
    print("  P%-2d %8.1f %8.1f %6.1f | %6.1f %5.1f %6.1f%s" % (
        i + 1, v[0], v[1], v[2], v[3], v[4], v[5],
        "  <-- 插入" if p.get("_ins") else ""))
