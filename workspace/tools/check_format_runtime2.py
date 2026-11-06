#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行时校验（改进版）：从 test.py 源码里【真正读出】顶层常量，再求值所有格式串。
   这样不会像我上一版那样用硬编码替身值而给出误导性结果。"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
tree = ast.parse(src)
lines = src.splitlines()

# ---- 1) 从源码顶层取出所有字面量常量 ----
env = {'NL': chr(10)}
consts = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        try:
            val = ast.literal_eval(node.value)
        except Exception:  # noqa: BLE001
            continue
        consts[name] = val
        env[name] = val
print('--- 从源码读到的顶层常量 ---')
for k in sorted(consts):
    print('  %-22s = %r' % (k, consts[k]))
print('')

# ---- 2) 求值所有 "字面量 % 参数" ----
ok = skip = bad = 0
for node in ast.walk(tree):
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)):
        continue
    left = node.left
    if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
        continue
    try:
        eval(compile(ast.Expression(body=node), '<f>', 'eval'), dict(env))  # noqa: S307
        ok += 1
    except (NameError, AttributeError):
        skip += 1
    except (TypeError, ValueError, KeyError) as e:
        bad += 1
        print('  !! L%-4d %s: %s\n        %s' % (node.lineno, type(e).__name__, e,
                                                 lines[node.lineno - 1].strip()[:76]))
print('格式串求值：成功 %d，跳过 %d（需运行时名），失败 %d  %s'
      % (ok, skip, bad, '✓' if bad == 0 else '✗'))

# ---- 3) 构造 GUI 说明文字，确认数字已跟随常量 ----
print('')
print('--- GUI 说明文字（用源码真实常量构造）---')
gui = None
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'Label':
        for kw in node.keywords:
            if kw.arg == 'text':
                gui = kw.value
if gui is None:
    print('  未找到')
else:
    ast.fix_missing_locations(ast.Expression(body=gui))
    s = eval(compile(ast.Expression(body=gui), '<g>', 'eval'), dict(env))  # noqa: S307
    print('  ✓ 构造成功（%d 字符 / %d 行）' % (len(s), s.count(chr(10)) + 1))
    for ln in s.split(chr(10)):
        print('     ' + ln)

# ---- 4) 也构造启动日志首行，核对速度与延时 ----
print('')
print('--- 启动日志里与速度/延时相关的行（用真实常量构造）---')
for node in ast.walk(tree):
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)):
        continue
    left = node.left
    if isinstance(left, ast.Constant) and isinstance(left.value, str) and \
            ('速度' in left.value or '延时' in left.value):
        try:
            v = eval(compile(ast.Expression(body=node), '<l>', 'eval'), dict(env))  # noqa: S307
            print('  L%-4d %s' % (node.lineno, v.strip()))
        except NameError:
            print('  L%-4d (需运行时名，跳过) %s' % (node.lineno, left.value.strip()[:60]))
        except Exception:  # noqa: BLE001
            pass
