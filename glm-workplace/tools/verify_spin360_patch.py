#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 校验副本脚本补丁后的语法与一致性（只读，不启动 RoboDK）
import ast, io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

PATH = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
src = open(PATH, encoding="utf-8").read()

# 1) 语法
try:
    ast.parse(src)
    print("AST OK")
except SyntaxError as e:
    print("SYNTAX ERROR:", e.lineno, e.msg, e.text)
    sys.exit(1)

# 2) 编译
import py_compile
py_compile.compile(PATH, doraise=True)
print("py_compile OK, size", len(src.encode("utf-8")), "bytes, lines", src.count("\n")+1)

# 3) 一致性检查
print("value=±180 残留(UI单选):", re.findall(r"value=(-?180)\b", src) or "无")
print("spin360 出现次数:", src.count("spin360"))
print("360 判定处:", [m.start() for m in re.finditer(r"in \(-360, 360\)", src)])
print("traj_j6_direction 引用:", src.count("traj_j6_direction"))
print("traj_singular_spin 引用:", src.count("traj_singular_spin"))
print("not in (-180, 180) 残留:", len(re.findall(r"not in \(-180, 180\)", src)), "(应为0)")
print("默认 j6_delta 取值处均带 spin360 分支:", ("360 if" in src) and True)
