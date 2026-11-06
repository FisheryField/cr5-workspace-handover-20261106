#!/usr/bin/env python3
"""恢复探针：读取工具几何顶点色，恢复工具原色；并测 Trace 颜色参数。"""
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
tools = RDK.ItemList(ITEM_TYPE_TOOL)
tool = tools[0]
print("tool:", tool.Name())
cur = tool.getColor()
print("当前颜色(getColor):", cur)
# 门把手_bs1 是 CAD 拖进来的工具，原色大概率是 STL 默认灰
# setColor 无 alpha=None 时会保留 alpha；用 setParam 试试恢复
for cmd, val in [
    ("TraceColor", "yellow"),
    ("Trace_Color", "yellow"),
]:
    try:
        RDK.Command(cmd, val)
        print("Command ok:", cmd)
    except Exception as e:
        print("Command fail:", cmd, e)
