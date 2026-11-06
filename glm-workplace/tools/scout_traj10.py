#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 只读侦查：找到轨迹8/9/10的JSON并dump + 探测当前工作站状态（轮位/父节点/关节/宏名）
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

roots = [r"D:\mydata\working things\dobot_arm", r"D:\mydata\glm-workplace"]
hits = []
for root in roots:
    for dp, dn, fn in os.walk(root):
        if "__pycache__" in dp:
            continue
        for f in fn:
            if "轨迹" in f and f.lower().endswith(".json"):
                p = os.path.join(dp, f)
                hits.append((p, os.path.getsize(p)))
print("== 轨迹JSON 清单 ==")
for p, s in sorted(hits):
    print("%9d  %s" % (s, p))

def dump(path):
    print("\n==== %s ====" % path)
    data = json.load(open(path, encoding="utf-8"))
    for i, it in enumerate(data, 1):
        v = it.get("values")
        vs = " ".join("%9.3f" % x for x in v) if isinstance(v, list) else str(v)
        print("P%-3d %-5s %s  sing=%-5s spin=%-5s d=%s" % (
            i, it.get("type"), vs, it.get("singular"), it.get("spin360"), it.get("j6_delta")))
    return data

datas = {}
for name in ("连续轨迹8", "连续轨迹9", "连续轨迹10"):
    for p, s in hits:
        if os.path.basename(p) == name + ".json":
            datas[name] = dump(p)
            break
    else:
        print("\n!! 未找到 %s.json" % name)

# 10 是否等于 8+9 首尾相接（只比 type/values/singular/spin/j6_delta）
if all(k in datas for k in ("连续轨迹8", "连续轨迹9", "连续轨迹10")):
    def key(it):
        return (it.get("type"), [round(float(x), 6) for x in it.get("values", [])],
                bool(it.get("singular")), bool(it.get("spin360")), it.get("j6_delta"))
    cat = [key(x) for x in datas["连续轨迹8"]] + [key(x) for x in datas["连续轨迹9"]]
    ten = [key(x) for x in datas["连续轨迹10"]]
    print("\n== 10 == 8+9 拼接? ", cat == ten)
    if cat != ten:
        print("  8+9 拼接共 %d 点，10 实际 %d 点" % (len(cat), len(ten)))
        for i, (a, b) in enumerate(zip(cat, ten), 1):
            if a != b:
                print("  首个差异 P%d:\n    8+9: %s\n    10  : %s" % (i, a, b))
                break

print("\n== 工作站状态 ==")
try:
    from robodk.robolink import *
    RDK = Robolink()
    st = RDK.Item('', ITEM_TYPE_STATION)
    print("station:", st.Name())
    robot = RDK.Item('', ITEM_TYPE_ROBOT)
    print("joints :", ["%.3f" % j for j in robot.Joints().list()[:6]])
    wheel = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
    w = wheel.PoseAbs()
    print("wheel parent:", wheel.Parent().Name())
    print("wheel PoseAbs t:", ["%.2f" % x for x in w.Pos()])
    B = robot.Parent().PoseAbs()
    wb = B.inv() * w
    print("wheel 基座系 t:", ["%.2f" % x for x in wb.Pos()])
    print("programs:")
    for it in RDK.ItemList(ITEM_TYPE_PROGRAM):
        try:
            print("   ", it.Name(), "| type", it.Type())
        except Exception:
            pass
except Exception as e:
    print("robolink probe failed:", type(e).__name__, e)
