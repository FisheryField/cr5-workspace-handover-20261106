#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对 test.py 里的 P1/P2 与 连续轨迹3.json 的前两点是否一字不差。"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = r'D:\mydata\working things\dobot_arm\RoboDK files 2'
traj = json.load(io.open(D + r'\连续轨迹3.json', encoding='utf-8'))
src = io.open(D + r'\test.py', encoding='utf-8').read()

print('连续轨迹3.json 共 %d 个点：' % len(traj))
for i, rec in enumerate(traj, 1):
    mark = '  ← P%d' % i if i <= 2 else ''
    print('  P%-2d %-5s %s%s' % (i, rec['type'], rec['values'], mark))
print('')
ok = True
for i, name in ((0, 'P1_TCP'), (1, 'P2_TCP')):
    m = re.search(re.escape(name) + r' = \[([^\]]+)\]', src)
    a = [float(x) for x in m.group(1).split(',')]
    b = [float(v) for v in traj[i]['values']]
    same = a == b
    ok = ok and same
    print('  %-7s 脚本 = %s' % (name, a))
    print('  %-7s 轨迹 = %s   -> %s' % ('', b, '一字不差 ✓' if same else '不一致 ✗'))
print('')
print('结论：%s' % ('P1/P2 与轨迹3 前两点完全一致 ✓' if ok else '存在差异 ✗'))
