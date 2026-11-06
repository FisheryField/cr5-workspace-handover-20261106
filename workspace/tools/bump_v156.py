#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版本号 v15.5 -> v15.6。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)
reps = [
    ("LOG_VERSION = 'v15.5-20261103'", "LOG_VERSION = 'v15.6-20261103'"),
    ('（P2P v15.5）', '（P2P v15.6）'),
    ('连续运动（P2P v15.5）', '连续运动（P2P v15.6）'),
    ('# 下次改动 ⇒ v15.6；标题与下方"连续运动"横幅要同步改',
     '# v15.6 ：_require_joints 改【带重试的稳定判定】（治 P8 尾通过 → P9 开头又失败：中间还在微动）\n'
     '                               # 下次改动 ⇒ v15.7；标题与下方"连续运动"横幅要同步改'),
]
for a, b in reps:
    print('  %-44s %d 次' % (a[:44].replace('\n', ' '), s.count(a)))
    s = s.replace(a, b)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('  字节: %d -> %d' % (n0, len(s)))
for k in ("LOG_VERSION = 'v15.6-20261103'", '（P2P v15.6）', '连续运动（P2P v15.6）',
          '带重试的稳定判定', '_tries=3'):
    print('    %-38s %s' % (k[:38], 'OK' if k in s else 'MISSING !!'))
