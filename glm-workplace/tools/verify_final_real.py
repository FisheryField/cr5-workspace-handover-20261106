#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 终验：站内宏替换后的完整状态 + 升级代码结构复查
import sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink

RDK = Robolink()

print("== 站内 Python 宏项（Type=10）==")
for it in RDK.ItemList():
    try:
        if it.Type() == 10:
            print("  " + it.Name())
    except Exception:
        pass

prog = RDK.Item("TCP真实运动")
code = prog.setParam("Code").replace("<br>", "\n")
tree = ast.parse(code)
funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
print("\nTCP真实运动：", len(code), "字符，", len(code.splitlines()), "行，", len(funcs), "个函数，语法 OK")

required = ["_retreat_orientation_records", "_plan_continuous_trajectory", "_checked_j6_rewinds",
            "_linear_path_endpoint", "_linear_path_endpoint_uncached", "_obstacle_joint_target",
            "_obstacle_joint_target_uncached", "_movej_test_cached", "_tcp_target_to_flange",
            "_flange_target_description", "_controller_feedback", "_live_joints",
            "_move_with_completion_check", "_execute_checked_real", "_validated_records"]
missing = [f for f in required if f not in funcs]
print("必需函数齐全:", not missing, ("缺:" + str(missing)) if missing else "")
print("自转360支持:", "spin360" in code, "；退让展开接入:", "_retreat_orientation_records(records)" in code)
print("_plan_cache 定义:", "_plan_cache = {}" in code)

# 与磁盘升级版源逐字核对
src = io.open(r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py", encoding="utf-8").read()
print("站内代码 == 磁盘升级版源:", code == src)
