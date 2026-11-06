#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态校验 test.py 里所有 "字面量 % 参数" 形式的格式串：
   统计左侧占位符数量，与右侧参数数量比对；不一致就报出来。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
tree = ast.parse(src)
print('语法 = PASS   字节数 = %d' % len(src.encode('utf-8')))

# 匹配 %[(name)][flags][width][.prec][len]type ；%% 跳过
SPEC = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?[hlL]?[diouxXeEfFgGcrsa%]')


def count_specs(s):
    n = 0
    for m in SPEC.finditer(s):
        if m.group(0) == '%%':
            continue
        n += 1
    return n


bad = 0
total = 0
for node in ast.walk(tree):
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)):
        continue
    left = node.left
    if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
        continue
    # 拼接的隐式字符串在 AST 里已是单个 Constant
    total += 1
    n_spec = count_specs(left.value)
    right = node.right
    if isinstance(right, ast.Tuple):
        n_args = len(right.elts)
    else:
        n_args = 1
    # 带名字的 %(x)s 形式另行处理（本文件未使用）
    if '%(' in left.value:
        mark = '（带名字，跳过）'
        ok = True
    else:
        ok = (n_spec == n_args)
        mark = ''
    if not ok:
        bad += 1
        snippet = left.value.replace('\n', ' ')[:70]
        print('  !! L%-4d 占位符=%d 参数=%d  %s%s' % (node.lineno, n_spec, n_args, snippet, mark))
    else:
        snippet = left.value.replace('\n', ' ')[:60]
        print('  ok L%-4d 占位符=%d 参数=%d  %s' % (node.lineno, n_spec, n_args, snippet))

print('')
print('共检查 %d 处格式串，其中不一致 %d 处 %s' % (total, bad, '✓ 全部通过' if bad == 0 else '✗ 需修'))
