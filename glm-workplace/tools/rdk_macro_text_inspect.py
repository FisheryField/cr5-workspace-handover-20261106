#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Inspect what setParam('Script') returned and whether the macro code survived.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

RDK = robolink.Robolink()
macro = RDK.Item("机械臂TCP仿真_副本")
v = macro.setParam("Script")
print("len:", len(v) if v else 0)
if v:
    print("--- first 400 ---")
    print(v[:400])
    print("--- last 200 ---")
    print(v[-200:])
    print("has wheel whitelist:", "磨砂圆柱_R180_H40" in v)
    print("has guard patch:", "'collision' in message.lower()" in v)

# compare with the ORIGINAL macro (the running 'TCP' block) for reference
ref = RDK.Item("TCP")
for it in RDK.ItemList():
    if it.Type() == robolink.ITEM_TYPE_MACRO and it.Name() != "机械臂TCP仿真_副本":
        try:
            rv = it.setParam("Script")
        except Exception:
            rv = None
        print("macro '%s' script len: %s" % (it.Name(), len(rv) if rv else 0))
