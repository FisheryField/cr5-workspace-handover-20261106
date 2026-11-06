#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 写回站内宏：1) 站内备份原项 2) setParam("Code") 写入升级代码 3) 读回比对
# 只改站内程序项，绝不保存工作站、绝不碰控制器。
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink

SRC = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"
new_code = io.open(SRC, encoding="utf-8").read()
print("升级代码:", len(new_code), "字符", len(new_code.splitlines()), "行")

RDK = Robolink()
prog = RDK.Item("TCP真实运动")
assert prog.Type() == 10, "目标不是 Python 宏项"

# 1) 站内备份（树内复制，不动磁盘）
stamp = time.strftime("%Y%m%d_%H%M%S")
prog.Copy()
backup = RDK.Paste()
backup.setName("TCP真实运动_升级前备份_" + stamp)
print("站内备份完成:", backup.Name())

# 2) 写入新代码
ret = prog.setParam("Code", new_code)
print("写入返回:", str(ret)[:80])

# 3) 读回比对
back = prog.setParam("Code")
back_norm = back.replace("<br>", "\n")
same = back_norm == new_code
print("读回长度:", len(back), "-> 归一后", len(back_norm), "；与源完全一致:", same)
if not same:
    import difflib
    a, b = new_code.splitlines(), back_norm.splitlines()
    print("行数: 源", len(a), "读回", len(b))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    print("相似度 %.6f" % sm.ratio())
    for o in sm.get_opcodes():
        if o[0] != "equal":
            print(o[0], "源[%d:%d] 读回[%d:%d]" % (o[1], o[2], o[3], o[4]))
            for l in a[o[1]:min(o[2], o[1] + 3)]:
                print("  源  |", l[:100])
            for l in b[o[3]:min(o[4], o[3] + 3)]:
                print("  读回|", l[:100])
            break
print("备份项仍在:", RDK.Item("TCP真实运动_升级前备份_" + stamp).Name())
