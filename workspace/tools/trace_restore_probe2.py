#!/usr/bin/env python3
"""恢复工具颜色（用 ObjectBranch 逐面恢复? 先试 setParam('Color','Reset')）+ 检查 Command 候选。"""
from robodk.robolink import Robolink, ITEM_TYPE_TOOL

RDK = Robolink()
tools = RDK.ItemList(ITEM_TYPE_TOOL)
tool = tools[0]
print("tool:", tool.Name())
# 尝试把工具恢复为 RoboDK 默认灰（不透明）：
# 门把手_bs1 的原色未记录，先用常见 STL 默认 (0.7,0.7,0.7,1)
tool.setColor([0.7, 0.7, 0.7, 1])
print("已设回中性灰 0.7")
for cmd, val in [
    ("Trace", "Line"),
    ("TraceStyle", "Line"),
    ("TraceStyle", "0"),
    ("TraceStyle", "1"),
]:
    try:
        res = RDK.Command(cmd, val)
        print("Command(", cmd, ",", val, ") ->", res)
    except Exception as e:
        print("Command fail:", cmd, val, e)
