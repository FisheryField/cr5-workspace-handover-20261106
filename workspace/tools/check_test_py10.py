#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终核查：十点版 test.py。"""
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

print('--- 点常量（应 P1~P10）---')
for i in range(1, 11):
    n = 'P%d_TCP' % i
    m = re.search(r'^%s\s*=\s*(\[[^\]]*\])' % n, src, re.M)
    print('  %-10s %s' % (n, m.group(1) if m else 'MISSING !!'))
for n in ('P4_J6_DELTA', 'P8_J6_DELTA'):
    m = re.search(r'^%s\s*=\s*(.+)$' % n, src, re.M)
    print('  %-10s %s' % (n, m.group(1).strip() if m else 'MISSING !!'))

print('--- 位姿生成（p4/p8 不应有）---')
for n in ('p1', 'p2', 'p3', 'p5', 'p6', 'p7', 'p9', 'p10'):
    ok = ('%s = fanuc_to_pose(*%s_TCP)' % (n, n.upper())) in src
    print('  %-4s %s' % (n, 'OK' if ok else 'MISSING !!'))
print('  p4/p8: %s' % ('OK（未生成）' if ('p4 = fanuc_to_pose' not in src and 'p8 = fanuc_to_pose' not in src) else '!! 存在'))

print('--- 段块（每段 预检 → 运动）---')
starts = [(i, ln.strip()) for i, ln in enumerate(lines, 1)
          if re.match(r'^# ---- 段 \d+ / \d+', ln.strip())]
starts.append((len(lines) + 1, '(文件末)'))
allok = True
for k in range(len(starts) - 1):
    lo, title = starts[k]
    hi = starts[k + 1][0]
    blk = '\n'.join(lines[lo - 1:hi - 1])
    nc = blk.count('_do_segment_check(')
    nm = blk.count('_move_one(')
    ns = blk.count('_run_singular_segment(')
    if ns:
        ok = (ns >= 1 and nm >= 1)
        kind = '奇异点(助手内含预检)'
    else:
        ok = (nc >= 1 and nm >= 1)
        kind = '普通'
    allok = allok and ok
    print('  L%-4d %-40s 预检=%d 运动=%d 助手=%d  %s %s'
          % (lo, title[:40], nc, nm, ns, kind, 'OK' if ok else '!! 异常'))
print('  全部段: %s' % ('OK ✓' if allok else '!! 有异常'))

print('--- 危险项 ---')
print('  ITEM_TYPE_TOOL = %d（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
