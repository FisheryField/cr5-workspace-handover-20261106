#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版本号 v15.8 -> v15.9。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)
reps = [
    ("LOG_VERSION = 'v15.8-20261103'", "LOG_VERSION = 'v15.9-20261103'"),
    ('（P2P v15.8）', '（P2P v15.9）'),
    ('连续运动（P2P v15.8）', '连续运动（P2P v15.9）'),
    ('# 下次改动 ⇒ v15.9；标题与下方"连续运动"横幅要同步改',
     '# v15.9 ：P8 也禁直发（治"选解自由"：J1/J6 同步偏 9.77° = 另一组 IK 解）⇒ P8 走细分\n'
     '                               # 下次改动 ⇒ v15.10；标题与下方"连续运动"横幅要同步改'),
]
for a, b in reps:
    print('  %-44s %d 次' % (a[:44].replace('\n', ' '), s.count(a)))
    s = s.replace(a, b)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('  字节: %d -> %d' % (n0, len(s)))
for k in ("LOG_VERSION = 'v15.9-20261103'", '（P2P v15.9）', '连续运动（P2P v15.9）',
          'MOVL_DIRECT_BLOCK_POINTS = (8, 9)'):
    print('    %-38s %s' % (k[:38], 'OK' if k in s else 'MISSING !!'))
