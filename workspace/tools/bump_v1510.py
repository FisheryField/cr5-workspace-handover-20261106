#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版本号 v15.9 -> v15.10，并把 P8 从禁直发名单恢复（P8 本来就是 MoveJ 段）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)
reps = [
    ("LOG_VERSION = 'v15.9-20261103'", "LOG_VERSION = 'v15.10-20261103'"),
    ('（P2P v15.9）', '（P2P v15.10）'),
    ('连续运动（P2P v15.9）', '连续运动（P2P v15.10）'),
    ('MOVL_DIRECT_BLOCK_POINTS = (8, 9)', 'MOVL_DIRECT_BLOCK_POINTS = (9,)'),
    ('# 下次改动 ⇒ v15.10；标题与下方"连续运动"横幅要同步改',
     '# v15.10：_require_joints 失败时【主动发 MoveJ 校正】（根治 P8 后不动：断连分支对 MoveJ 只等静止不等到位）\n'
     '                               # 下次改动 ⇒ v15.11；标题与下方"连续运动"横幅要同步改'),
]
for a, b in reps:
    print('  %-44s %d 次' % (a[:44].replace('\n', ' '), s.count(a)))
    s = s.replace(a, b)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('  字节: %d -> %d' % (n0, len(s)))
for k in ("LOG_VERSION = 'v15.10-20261103'", '（P2P v15.10）', '连续运动（P2P v15.10）',
          '主动发 MoveJ 校正', 'MOVL_DIRECT_BLOCK_POINTS = (9,)'):
    print('    %-40s %s' % (k[:40], 'OK' if k in s else 'MISSING !!'))
