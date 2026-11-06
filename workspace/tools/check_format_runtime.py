#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行时校验：把 test.py 里所有 "字面量 % 参数" 的表达式抽出来真求值，
   能算通就说明占位符与参数匹配（这比静态计数可靠，能处理函数调用形式的参数）。"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
tree = ast.parse(src)
lines = src.splitlines()

# 提供常用名的最小替身，避免真启动 tkinter / robodk
env = {
    'NL': chr(10),
    'SEG_DELAY': 2.0,
    'P4_J6_DELTA': 180.0,
    'P8_J6_DELTA': 180.0,
    'ROBOT_SPEED': 10.0,
}

ok = bad = skip = 0
for node in ast.walk(tree):
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)):
        continue
    left = node.left
    if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
        continue
    expr = ast.Expression(body=node)
    ast.fix_missing_locations(expr)
    try:
        code = compile(expr, '<frag>', 'eval')
        val = eval(code, dict(env))  # noqa: S307
        ok += 1
    except NameError as e:
        skip += 1
        print('  [跳过] L%-4d 需要外部名: %s' % (node.lineno, e))
    except (TypeError, ValueError, KeyError) as e:
        bad += 1
        snippet = lines[node.lineno - 1].strip()[:78]
        print('  !! L%-4d %s: %s\n        %s' % (node.lineno, type(e).__name__, e, snippet))

print('')
print('求值成功 %d 处，跳过 %d 处，失败 %d 处 %s'
      % (ok, skip, bad, '✓ 全部通过' if bad == 0 else '✗ 需修'))

# 再单独验证 GUI 那段 text= 是否可构造（不启动 tkinter）
print('')
print('--- 单独验证 GUI 说明文字 ---')
m = None
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'Label':
        for kw in node.keywords:
            if kw.arg == 'text':
                m = kw.value
                break
if m is None:
    print('  未找到 tk.Label(text=...)')
else:
    ast.fix_missing_locations(ast.Expression(body=m))
    try:
        s = eval(compile(ast.Expression(body=m), '<gui>', 'eval'), dict(env))  # noqa: S307
        print('  ✓ 构造成功，共 %d 字符、%d 行' % (len(s), s.count(chr(10)) + 1))
        for ln in s.split(chr(10)):
            print('     ' + ln)
    except Exception as e:  # noqa: BLE001
        print('  ✗ 失败: %s: %s' % (type(e).__name__, e))
