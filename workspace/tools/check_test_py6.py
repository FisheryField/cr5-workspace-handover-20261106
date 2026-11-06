#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查六点版 test.py 的完整性。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
ast.parse(src)
print('字节数 = %d   语法 = PASS' % len(src.encode('utf-8')))

print('--- 六个点常量 ---')
for n in ('P1_TCP', 'P2_TCP', 'P3_TCP', 'P4_TCP', 'P5_TCP', 'P6_TCP', 'P4_J6_DELTA'):
    m = re.search(r'^%s\s*=\s*(.+)$' % n, src, re.M)
    print('  %-14s %s' % (n, m.group(1).strip() if m else 'MISSING !!'))

print('--- 位姿生成（P4 故意不生成）---')
for n in ('p1', 'p2', 'p3', 'p5', 'p6'):
    ok = ('%s = fanuc_to_pose(*%s_TCP)' % (n, n.upper())) in src
    print('  %-4s %s' % (n, 'OK' if ok else 'MISSING !!'))
print('  P4 不应有位姿生成: %s' % ('OK' if 'p4 = fanuc_to_pose' not in src else '!! 存在'))

print('--- 段标题 ---')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if re.match(r'^log\("--- 段', t) or re.match(r'^# ---- 段', t):
        print('  L%-4d %s' % (i, t[:74]))

print('--- 预检 / 运动（应按 L 递增交替）---')
seq = []
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if t.startswith('def'):
        continue
    if '_do_segment_check(' in t:
        seq.append((i, '预检'))
    if '_move_one(' in t:
        seq.append((i, '运动'))
for i, k in seq:
    print('  L%-4d %s' % (i, k))
ok = all(seq[k][1] == ('预检' if k % 2 == 0 else '运动') for k in range(len(seq)))
print('  交替正确: %s（共 %d 项）' % ('是' if ok else '否 !!', len(seq)))

print('--- 危险项 ---')
print('  ITEM_TYPE_TOOL = %d（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
