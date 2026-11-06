#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复核 test.py：语法、关键函数、调用顺序、以及"字符串内半角引号"隐患扫描。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
print('文件字节数 =', len(src.encode('utf-8')))
tree = ast.parse(src)
print('[1] 语法: PASS')

funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
for w in ('_enable_obstacle_checks', '_check_segment', '_ik_candidates',
          '_obstacle_posture_key', '_movej_test_cached', '_do_segment_check',
          '_move_one', '_worker'):
    print('    %-26s %s' % (w, 'OK' if w in funcs else 'MISSING !!'))

print('[2] 关键调用:')
for s in ('SolveIK_All', 'MoveJ_Test', 'setCollisionActivePair', 'setCollisionActive(',
          'JointPoses', 'JointLimits', 'CollisionPairs'):
    print('    %-24s %d 次' % (s, src.count(s)))

print('[3] 末端工具/磨砂（应只出现在注释文字里）:')
for s in ('ITEM_TYPE_TOOL', '磨砂', '圆盘'):
    print('    %-18s %d 次' % (s, src.count(s)))

print('[4] 调用顺序:')
for i, ln in enumerate(src.splitlines(), 1):
    t = ln.strip()
    if '_do_segment_check(' in t and not t.startswith('def'):
        print('    L%-4d 预检: %s' % (i, t[:76]))
    if '_move_one(' in t and not t.startswith('def'):
        print('    L%-4d 运动: %s' % (i, t[:76]))

# 5) 隐患扫描：字符串里出现半角引号导致提前闭合（能通过 ast 就说明没问题，这里再报可疑行）
print('[5] 可能含全角/半角引号混用的中文行（供人工确认）:')
pat = re.compile(r'[\u201c\u201d]')
n = 0
for i, ln in enumerate(src.splitlines(), 1):
    if pat.search(ln) and 'log(' in ln or ('log(' in ln and pat.search(ln)):
        print('    L%-4d %s' % (i, ln.strip()[:90]))
        n += 1
print('    共 %d 行（这些是合法的全角引号，仅提示）' % n)
