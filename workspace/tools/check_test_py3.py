#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查加入 P3 后的 test.py。"""
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

print('[2] 三个目标点:')
for name in ('P1_TCP', 'P2_TCP', 'P3_TCP'):
    m = re.search(r'^%s\s*=\s*(\[[^\]]*\])' % name, src, re.M)
    print('    %-8s %s' % (name, m.group(1) if m else 'MISSING !!'))

print('[3] p1/p2/p3 生成:')
for name in ('p1', 'p2', 'p3'):
    print('    %-3s = fanuc_to_pose(*%s_TCP)   %s'
          % (name, name.upper(), 'OK' if ('%s = fanuc_to_pose(*%s_TCP)' % (name, name.upper())) in src else 'MISSING !!'))

print('[4] 段编号与调用顺序:')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if re.match(r'^log\("--- 段', t):
        print('    L%-4d %s' % (i, t[:70]))
    if '_do_segment_check(' in t and not t.startswith('def'):
        print('    L%-4d 预检: %s' % (i, t[:74]))
    if '_move_one(' in t and not t.startswith('def'):
        print('    L%-4d 运动: %s' % (i, t[:74]))

print('[5] P3 出现位置:')
for i, ln in enumerate(src.splitlines(), 1):
    if 'P3' in ln:
        print('    L%-4d %s' % (i, ln.strip()[:88]))

print('[6] 危险项:')
print('    磨砂/圆盘 只应出现在注释/日志: %d 次' % (src.count('磨砂') + src.count('圆盘')))
print('    ITEM_TYPE_TOOL: %d 次（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
