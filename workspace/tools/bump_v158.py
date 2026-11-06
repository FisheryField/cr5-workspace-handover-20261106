#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版本号 v15.7 -> v15.8。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)
reps = [
    ("LOG_VERSION = 'v15.7-20261103'", "LOG_VERSION = 'v15.8-20261103'"),
    ('（P2P v15.7）', '（P2P v15.8）'),
    ('连续运动（P2P v15.7）', '连续运动（P2P v15.8）'),
    ('# 下次改动 ⇒ v15.8；标题与下方"连续运动"横幅要同步改',
     '# v15.8 ：★直发落点【自干涉安全网】—— 控制器自行选解可能落进禁区 ⇒ 立刻回认证构型\n'
     '                               # 下次改动 ⇒ v15.9；标题与下方"连续运动"横幅要同步改'),
]
for a, b in reps:
    print('  %-44s %d 次' % (a[:44].replace('\n', ' '), s.count(a)))
    s = s.replace(a, b)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('  字节: %d -> %d' % (n0, len(s)))
for k in ("LOG_VERSION = 'v15.8-20261103'", '（P2P v15.8）', '连续运动（P2P v15.8）',
          '直发落点落入自干涉禁区'):
    print('    %-38s %s' % (k[:38], 'OK' if k in s else 'MISSING !!'))
