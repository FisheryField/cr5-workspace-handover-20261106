#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 函数级 diff：TCP仿真_副本.py vs TCP真实运动_当前.py
import io, sys, ast, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

SIM = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
REAL = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_当前.py"

def load(path):
    src = io.open(path, encoding="utf-8", errors="replace").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    funcs, consts = {}, {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            body = "\n".join(l.rstrip() for l in lines[n.lineno - 1:n.end_lineno])
            funcs[n.name] = body
        elif isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            nm = n.targets[0].id
            if nm.isupper():
                try:
                    consts[nm] = ast.literal_eval(n.value)
                except Exception:
                    consts[nm] = "<expr>"
    return funcs, consts

fs, cs = load(SIM)
fr, cr = load(REAL)

print("== 常量差异 ==")
for k in sorted(set(cs) | set(cr)):
    if cs.get(k) != cr.get(k):
        print("  %-38s 仿真=%-28r 真实=%r" % (k, cs.get(k, "<缺>"), cr.get(k, "<缺>")))

only_s = sorted(set(fs) - set(fr))
only_r = sorted(set(fr) - set(fs))
print("\n== 仅仿真有（%d 个）==" % len(only_s))
for n in only_s:
    print("  " + n)
print("\n== 仅真实有（%d 个）==" % len(only_r))
for n in only_r:
    print("  " + n)

print("\n== 同名但内容不同 ==")
diff_names = [n for n in sorted(set(fs) & set(fr)) if fs[n] != fr[n]]
for n in diff_names:
    sm = difflib.SequenceMatcher(None, fs[n].splitlines(), fr[n].splitlines(), autojunk=False)
    print("  %-42s 相似度 %.3f" % (n, sm.ratio()))

print("\n== 同名且一致 ==")
same = [n for n in sorted(set(fs) & set(fr)) if fs[n] == fr[n]]
print("  " + (", ".join(same) if same else "（无）"))
