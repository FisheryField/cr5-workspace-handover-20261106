#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 P2P 脚本版本号从 v15.3 升到 v15.4（三处同步）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)

reps = [
    ("LOG_VERSION = 'v15.3-20261103'", "LOG_VERSION = 'v15.4-20261103'"),
    ('（P2P v15.3）', '（P2P v15.4）'),
    ('连续运动（P2P v15.3）', '连续运动（P2P v15.4）'),
    ('# 下次改动 ⇒ v15.4；标题与下方"连续运动"横幅要同步改',
     '# v15.4 ：收口 MoveJ 加重试（治 P8 停下：收口遇断连没走完 ⇒ 关节残差 2.68° 残留）\n'
     '                               # 下次改动 ⇒ v15.5；标题与下方"连续运动"横幅要同步改'),
]
for a, b in reps:
    cnt = s.count(a)
    print('  替换 %-40s 出现 %d 次' % (a[:40].replace('\n', ' '), cnt))
    s = s.replace(a, b)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('  字节: %d -> %d' % (n0, len(s)))
print('  三处版本号检查:')
for k in ("LOG_VERSION = 'v15.4-20261103'", '（P2P v15.4）', '连续运动（P2P v15.4）'):
    print('    %-34s %s' % (k[:34], 'OK' if k in s else 'MISSING !!'))
