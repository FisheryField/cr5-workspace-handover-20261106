#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 重新换入站内宏：AddFile(更新后的升级版) -> 交换名字 -> 旧项改名归档；读回校验。
# 不保存工作站、不碰控制器。
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink

SRC = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"
new_code = io.open(SRC, encoding="utf-8").read()

RDK = Robolink()
old = RDK.Item("TCP真实运动")
stamp = time.strftime("%Y%m%d_%H%M%S")

new_item = RDK.AddFile(SRC)
ncode = new_item.setParam("Code").replace("<br>", "\n")
print("新宏代码与源一致:", ncode == new_code)
if ncode != new_code:
    print("!! 不一致，中止")
    sys.exit(1)

old.setName("TCP真实运动_偏离50版_" + stamp)
new_item.setName("TCP真实运动")
final = RDK.Item("TCP真实运动")
fcode = final.setParam("Code").replace("<br>", "\n")
print("站内 TCP真实运动 == 升级版源:", fcode == new_code)
print("默认偏离已是500:", 'value="500.0"' in fcode)
print("旧版归档为:", old.Name())
