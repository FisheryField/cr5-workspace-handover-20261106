#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 取 TCP真实运动 宏的代码与文件路径（只读）
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink

RDK = Robolink()
prog = RDK.Item("TCP真实运动")
print("找到项:", prog.Name(), "Type:", prog.Type())

code = prog.setParam("Code")
print("代码长度:", len(code), "字符")

# 站与宏路径线索
print("PATH_OPENSTATION:", RDK.getParam("PATH_OPENSTATION"))
try:
    print("Param File:", prog.setParam("File"))
except Exception as e:
    print("File param err:", repr(e)[:120])

dst = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_当前.py"
with open(dst, "w", encoding="utf-8") as f:
    f.write(code)
print("已导出到:", dst)
print("\n== 前 60 行 ==")
for i, l in enumerate(code.splitlines()[:60]):
    print("%4d| %s" % (i + 1, l))
print("\n== def/常量 清单 ==")
import ast
try:
    tree = ast.parse(code)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            print("def %-44s L%d-%d" % (n.name, n.lineno, n.end_lineno))
        elif isinstance(n, ast.Assign):
            t = n.targets[0]
            if isinstance(t, ast.Name) and (t.id.isupper() or t.id in ("_plan_cache",)):
                try:
                    print("VAR  %-44s = %r" % (t.id, ast.literal_eval(n.value)))
                except Exception:
                    print("VAR  %-44s = <expr>" % t.id)
except SyntaxError as e:
    print("!! 语法错误:", e)
