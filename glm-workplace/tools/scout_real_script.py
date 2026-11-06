#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 侦查当前站里的「TCP真实运动」脚本：类型、路径、内容（只读，不运行不保存）
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

RDK = Robolink()
prog = None
items = RDK.ItemList(list_names=False) if False else None
for it in RDK.ItemList():
    name = it.Name()
    itype = it.type() if callable(getattr(it, "type", None)) else None
    print("站内项: [%s] type=%s" % (name, itype))
    if "TCP" in name and ("真实" in name or "运动" in name):
        prog = it
if prog is None:
    print("!! 未找到 TCP 真实运动脚本")
    sys.exit(0)

print("\n== 目标脚本项 ==")
print("Name:", prog.Name(), " Type:", prog.Type())
try:
    p = prog.setParam("Path")
    print("Param Path:", p)
except Exception as e:
    print("Path param err:", e)
try:
    import os
    cand = []
    station_path = RDK.ActiveStation() if hasattr(RDK, "ActiveStation") else None
    print("ActiveStation attr:", station_path)
except Exception as e:
    print("station err:", e)
