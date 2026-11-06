#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在解出的 .rdk 文本里定位内嵌 Python 宏的条目结构。"""
import io, re

text = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt", encoding="utf-8").read()

print("== coding markers ==")
for m in re.finditer(r"# -\*- coding: utf-8 -\*-", text):
    print("  at char", m.start())

print("== 脚本名条目（站内 item 引用）==")
for m in re.finditer(r"(机械臂[^\"\n<>]{0,24}\.py|robodk_movej[^\"\n<>]{0,24}\.py|test\.py)", text):
    print("  name:", m.group(1), "at", m.start())

print("== RoboDK 条目树标记（Type/Name 行，截前后文）==")
# RoboDK 站文件里常见 <key>NAME</key> 或 name= 结构；先看 coding marker 前面的 300 字符
for m in re.finditer(r"# -\*- coding: utf-8 -\*-", text):
    ctx = text[max(0, m.start() - 400):m.start()]
    print("---- ctx before marker at", m.start(), "----")
    print(ctx[-380:])
    print()
