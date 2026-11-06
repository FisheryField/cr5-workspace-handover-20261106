#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终核查：八点版 test.py。按"段块"分组核验 预检→运动 的顺序。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
lines = src.splitlines()
ast.parse(src)
print('字节数 = %d   语法 = PASS' % len(src.encode('utf-8')))

print('--- 点常量 ---')
for n in ('P1_TCP', 'P2_TCP', 'P3_TCP', 'P4_TCP', 'P5_TCP', 'P6_TCP', 'P7_TCP', 'P8_TCP',
          'P4_J6_DELTA', 'P8_J6_DELTA', 'P4_IS_SINGULAR', 'P8_IS_SINGULAR'):
    m = re.search(r'^%s\s*=\s*(.+)$' % n, src, re.M)
    print('  %-16s %s' % (n, m.group(1).strip() if m else 'MISSING !!'))

print('--- 位姿生成 ---')
for n in ('p1', 'p2', 'p3', 'p5', 'p6', 'p7'):
    ok = ('%s = fanuc_to_pose(*%s_TCP)' % (n, n.upper())) in src
    print('  %-4s %s' % (n, 'OK' if ok else 'MISSING !!'))
print('  p4/p8 不应生成: %s' % ('OK' if ('p4 = fanuc_to_pose' not in src and 'p8 = fanuc_to_pose' not in src) else '!! 存在'))

print('--- 奇异点助手 ---')
print('  _singular_j6_target    : %s' % ('OK' if 'def _singular_j6_target' in src else 'MISSING !!'))
print('  _run_singular_segment  : %s' % ('OK' if 'def _run_singular_segment' in src else 'MISSING !!'))
# 助手内部必须"先 _do_segment_check 再 return"
m = re.search(r'def _run_singular_segment.*?\n(?=def |\Z)', src, re.S)
body = m.group(0) if m else ''
pos_check = body.find('_do_segment_check(')
pos_ret = body.find('return allow, start,')
print('  助手内部顺序: %s（_do_segment_check 在 return 之前）'
      % ('OK' if 0 <= pos_check < pos_ret else '!! 顺序异常'))

print('--- 段块（每段：预检 → 运动）---')
starts = [(i, ln.strip()) for i, ln in enumerate(lines, 1)
          if re.match(r'^# ---- 段 \d+ / \d+', ln.strip())]
starts.append((len(lines) + 1, '(文件末)'))
for k in range(len(starts) - 1):
    lo, title = starts[k]
    hi = starts[k + 1][0]
    blk = '\n'.join(lines[lo - 1:hi - 1])
    n_check = blk.count('_do_segment_check(')
    n_move = blk.count('_move_one(')
    n_sing = blk.count('_run_singular_segment(')
    kind = '奇异点(助手内含预检)' if n_sing else '普通'
    ok = (n_check >= 1 and n_move >= 1) if not n_sing else (n_sing >= 1 and n_move >= 1)
    print('  L%-4d %-34s 预检=%d 运动=%d 奇异助手=%d  %s %s'
          % (lo, title[:34], n_check, n_move, n_sing, kind, 'OK' if ok else '!! 异常'))

print('--- 危险项 ---')
print('  ITEM_TYPE_TOOL = %d（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
