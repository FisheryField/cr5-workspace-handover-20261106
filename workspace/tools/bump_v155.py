#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 P2P 脚本版本号从 v15.4 升到 v15.5（三处同步 + 历史注释）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)

reps = [
    ("LOG_VERSION = 'v15.4-20261103'", "LOG_VERSION = 'v15.5-20261103'"),
    ('（P2P v15.4）', '（P2P v15.5）'),
    ('连续运动（P2P v15.4）', '连续运动（P2P v15.5）'),
    ('# 下次改动 ⇒ v15.5；标题与下方"连续运动"横幅要同步改',
     '# v15.5 ：直发+收口后再做【关节校正重试】（治 P8 停下：收口走假断连分支 ⇒ 报"已完成"但关节没到位）\n'
     '                               # 下次改动 ⇒ v15.6；标题与下方"连续运动"横幅要同步改'),
]
for a, b in reps:
    c = s.count(a)
    print('  %-46s %d 次' % (a[:46].replace('\n', ' '), c))
    s = s.replace(a, b)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('  字节: %d -> %d' % (n0, len(s)))
for k in ("LOG_VERSION = 'v15.5-20261103'", '（P2P v15.5）', '连续运动（P2P v15.5）',
          '直发+收口后关节仍与预检不一致'):
    print('    %-40s %s' % (k[:40], 'OK' if k in s else 'MISSING !!'))
