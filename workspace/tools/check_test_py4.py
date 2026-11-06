#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查加入 P4（奇异点，仅 J6±180°）后的 test.py。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
print('文件字节数 =', len(src.encode('utf-8')))
ast.parse(src)
print('[1] 语法: PASS')

print('[2] 四个目标点与奇异点常量:')
for name in ('P1_TCP', 'P2_TCP', 'P3_TCP', 'P4_TCP', 'P4_IS_SINGULAR', 'P4_J6_DELTA'):
    m = re.search(r'^%s\s*=\s*(.+)$' % name, src, re.M)
    print('    %-16s %s' % (name, m.group(1).strip() if m else 'MISSING !!'))

print('[3] 段结构与调用顺序:')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if re.match(r'^log\("--- 段', t):
        print('    L%-4d %s' % (i, t[:76]))
    if '_do_segment_check(' in t and not t.startswith('def'):
        print('    L%-4d   预检: %s' % (i, t[:72]))
    if '_move_one(' in t and not t.startswith('def'):
        print('    L%-4d   运动: %s' % (i, t[:72]))

print('[4] P4 特异点关键代码:')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if any(k in t for k in ('j6_target', 'P4_J6_DELTA', 'P4_IS_SINGULAR', '不做 TCP', '跳过 IK')):
        print('    L%-4d %s' % (i, t[:96]))

print('[5] 危险项:')
print('    SolveIK 相关调用: %d 次（段4 不应新增）' % src.count('SolveIK'))
print('    MoveJ_Test: %d 次' % src.count('MoveJ_Test'))
print('    ITEM_TYPE_TOOL: %d 次（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
