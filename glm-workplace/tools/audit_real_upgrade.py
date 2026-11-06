#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 写回站内宏前的整体审查：名字解析、GUI 绑定、单点路径不受影响
import io, sys, ast, builtins
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

SRC = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"
src = io.open(SRC, encoding="utf-8").read()
tree = ast.parse(src)

# 1) 收集模块级绑定（函数/类/赋值/imports），再检查每个函数体内引用的名字
module_names = set(dir(builtins)) | {"RDK", "robot"}
for n in tree.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        module_names.add(n.name)
    elif isinstance(n, ast.Assign):
        for t in ast.walk(n):
            if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store):
                module_names.add(t.id)
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for a in n.names:
            module_names.add(a.asname or a.name.split(".")[0])
    elif isinstance(n, (ast.If, ast.Try)):
        for sub in ast.walk(n):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                module_names.add(sub.id)

problems = []
for n in tree.body:
    if not isinstance(n, ast.FunctionDef):
        continue
    params = {a.arg for a in n.args.args}
    locals_ = set(params)
    for sub in ast.walk(n):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            locals_.add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.Lambda, ast.comprehension)):
            pass
    # comprehension 目标也算局部
    for sub in ast.walk(n):
        if isinstance(sub, ast.comprehension):
            for t in ast.walk(sub.target):
                if isinstance(t, ast.Name):
                    locals_.add(t.id)
    for sub in ast.walk(n):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            nm = sub.id
            if nm not in locals_ and nm not in module_names:
                problems.append((n.name, nm, sub.lineno))

print("未解析名字:", problems if problems else "无")

# 2) GUI 绑定
for v in ("spin_var", "singular_var", "j6_direction_var", "real_deviation_var"):
    defs = src.count(v + " = ")
    uses = src.count(v)
    print("%-22s 定义 %d 次，引用 %d 次" % (v, defs, uses))

# 3) 单点路径：execute_single 调用 _execute_checked_real 时 single_method != None -> 不做退让展开
ok1 = "if single_method is None and len(records) > 1:" in src
print("单点不做退让展开守卫:", ok1)
# 4) _execute_checked_real 中 records 来源
idx = src.find("records = _validated_records(data)")
print("执行入口退让接入:", src[idx:idx + 260].replace("\n", " | ")[:260])
# 5) GUI 自转复选框
print("自转360复选框:", 'text="J6自转360°（第二类，六维与前点相同）"' in src)
# 6) 退让展开条件核对：单点导入时 records 也可能 >1 —— import_trajectory 不展开，执行时才展开
print("import_trajectory 不含退让调用:", "_retreat" not in src[src.find("def import_trajectory"):src.find("def delete_last_record")])
