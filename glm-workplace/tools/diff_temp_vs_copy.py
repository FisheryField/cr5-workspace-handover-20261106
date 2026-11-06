#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 比对用户 Temp 里实际运行的 TCP仿真8.py 与我维护的副本
import io, sys, difflib, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

P1 = r"C:/Users/FisheryField/AppData/Local/Temp/TCP仿真8.py"   # 用户实际运行
P2 = r"D:/mydata/glm-workplace/sim_scripts/机械臂TCP仿真_副本.py"  # 我的副本

s1 = io.open(P1, encoding="utf-8", errors="replace").read().splitlines()
s2 = io.open(P2, encoding="utf-8", errors="replace").read().splitlines()

# 1) 顶层常量对比（AST 层面，排除行号干扰）
def top_assigns(path):
    tree = ast.parse(io.open(path, encoding="utf-8", errors="replace").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper() or name in ("_plan_cache",):
                try:
                    out[name] = ast.literal_eval(node.value)
                except Exception:
                    out[name] = "<expr>"
    return out

a1, a2 = top_assigns(P1), top_assigns(P2)
keys = sorted(set(a1) | set(a2))
print("== 顶层常量差异（Temp版 vs 副本）==")
diff_n = 0
for k in keys:
    v1, v2 = a1.get(k, "<缺>"), a2.get(k, "<缺>")
    if v1 != v2:
        print("  %-34s Temp=%-24r 副本=%r" % (k, v1, v2))
        diff_n += 1
if diff_n == 0:
    print("  （全部一致）")

# 2) 逐函数对比
def top_funcs(path):
    tree = ast.parse(io.open(path, encoding="utf-8", errors="replace").read())
    res = {}
    lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            src = "\n".join(l.rstrip() for l in lines[node.lineno - 1:node.end_lineno])
            res[node.name] = (src, node.lineno, node.end_lineno)
    return res

f1, f2 = top_funcs(P1), top_funcs(P2)
only1 = sorted(set(f1) - set(f2))
only2 = sorted(set(f2) - set(f1))
print("\n== 仅 Temp 版有的函数 ==")
print("  " + (", ".join(only1) if only1 else "（无）"))
print("== 仅副本有的函数 ==")
print("  " + (", ".join(only2) if only2 else "（无）"))

print("\n== 两版都有但内容不同的函数 ==")
changed = []
for name in sorted(set(f1) & set(f2)):
    if f1[name][0] != f2[name][0]:
        changed.append(name)
for name in changed:
    _, l1a, l1b = f1[name]
    _, l2a, l2b = f2[name]
    print("  %-40s Temp:%d-%d行(%d行) 副本:%d-%d行(%d行)" % (name, l1a, l1b, l1b - l1a + 1, l2a, l2b, l2b - l2a + 1))

# 3) 对改动最大的函数给统一diff（最多2个）
for name in changed[:2]:
    print("\n== diff: %s （- Temp版 / + 副本）==" % name)
    d = list(difflib.unified_diff(f1[name][0].splitlines(), f2[name][0].splitlines(),
                                  lineterm="", n=1))
    for l in d[2:]:
        print("  " + l)
