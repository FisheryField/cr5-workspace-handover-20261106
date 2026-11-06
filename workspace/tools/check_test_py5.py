#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查加入 P5 后的 test.py。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
ast.parse(src)
print('字节数 = %d   语法 = PASS' % len(src.encode('utf-8')))

print('--- 常量 ---')
for n in ('P1_TCP', 'P2_TCP', 'P3_TCP', 'P4_TCP', 'P5_TCP', 'P4_J6_DELTA', 'P4_IS_SINGULAR'):
    m = re.search(r'^%s\s*=\s*(.+)$' % n, src, re.M)
    print('  %-16s %s' % (n, m.group(1).strip() if m else 'MISSING !!'))

print('--- p1/p3/p5 生成 ---')
for n in ('p1', 'p2', 'p3', 'p5'):
    ok = ('%s = fanuc_to_pose(*%s_TCP)' % (n, n.upper())) in src
    print('  %-4s %s' % (n, 'OK' if ok else 'MISSING !!'))

print('--- 段标题 ---')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if re.match(r'^log\("--- 段', t):
        print('  L%-4d %s' % (i, t[:72]))

print('--- 预检 / 运动 顺序 ---')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if t.startswith('def'):
        continue
    if '_do_segment_check(' in t:
        print('  L%-4d 预检  %s' % (i, t[:66]))
    if '_move_one(' in t:
        print('  L%-4d 运动  %s' % (i, t[:66]))

print('--- 危险项 ---')
print('  ITEM_TYPE_TOOL = %d（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
print('  磨砂+圆盘      = %d（注释/日志）' % (src.count('磨砂') + src.count('圆盘')))
