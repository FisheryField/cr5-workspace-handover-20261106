#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 方案B：AddFile 加宏项替换。步骤：
#  1) 验证已建备份项的代码完整
#  2) AddFile 升级版 py -> 新宏项，读回 Code 比对
#  3) 成功后：旧项改名为「TCP真实运动_旧版_时间戳」，新项改名为 TCP真实运动
# 全程不保存工作站、不碰控制器。
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink

SRC = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"
new_code = io.open(SRC, encoding="utf-8").read()

RDK = Robolink()

# 1) 备份项代码完整性
backup = RDK.Item("TCP真实运动_升级前备份_20261009_113242")
bcode = backup.setParam("Code").replace("<br>", "\n")
old = RDK.Item("TCP真实运动")
ocode = old.setParam("Code").replace("<br>", "\n")
print("备份项代码 == 旧项代码:", bcode == ocode, "(", len(bcode), "字符 )")

# 2) AddFile 新宏
new_item = RDK.AddFile(SRC)
print("AddFile -> Name:", new_item.Name(), "Type:", new_item.Type())
ncode = new_item.setParam("Code").replace("<br>", "\n")
print("新项代码长度:", len(ncode), "；与升级版源一致:", ncode == new_code)
if ncode != new_code:
    print("!! 新项代码与源不一致，停在交换前。前200字符：")
    print(ncode[:200])
    sys.exit(1)

# 3) 交换名字
stamp = time.strftime("%Y%m%d_%H%M%S")
old.setName("TCP真实运动_旧版_" + stamp)
new_item.setName("TCP真实运动")
final = RDK.Item("TCP真实运动")
fcode = final.setParam("Code").replace("<br>", "\n")
print("交换后：TCP真实运动 代码 == 升级版源:", fcode == new_code)
print("最终项 Type:", final.Type())
print("旧版保留为:", old.Name())
