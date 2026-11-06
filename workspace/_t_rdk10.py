# -*- coding: utf-8 -*-
"""从 .rdk 里按条目名取出每个脚本条目的 python 源码，并落盘到 _rdk_scripts/。"""
import hashlib, os, re, struct, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
OUT = r'D:\mydata\workspace\_rdk_scripts'
os.makedirs(OUT, exist_ok=True)

# 1) 所有 "script 条目名" —— 由 API 已知，逐个在二进制里找它的 UTF-16 出现位置
names = ['TCP真实运动_升级前备份_20260910_170410', '机械臂法兰真实运动',
         'TCP真实运动_到位复核前备份_20260910_172919', 'TCP真实运动_旧版_20261009_113434',
         'TCP仿真_退让换向升级前', 'TCP仿真', 'TCP真实运动_升级前备份_20261009_113242',
         'TCP真实运动_偏离50版_20261009_142831', 'TCP真实运动_偏离50版_20260910_144043',
         'TCP真实运动_偏离50版_20261009_144114', 'TCP真实运动_偏离50版_20261009_145211',
         'TCP真实运动_偏离50版_20261009_145243', 'TCP真实运动_偏离50版_20261009_145539',
         'TCP真实运动_偏离50版_20261009_150519', 'TCP真实运动_偏离50版_20261009_151311',
         'TCP真实运动_偏离50版_20261009_154907', 'TCP真实运动_偏离50版_20261009_154919',
         'TCP真实运动_偏离50版_20261009_164424', 'TCP真实运动', 'test', '方向角计算']

print('=== .rdk 内 UTF-16 名字出现位置 ===')
found = {}
for nm in names:
    b = nm.encode('utf-16-le')
    pos = d.find(b)
    found[nm] = pos
    print('  %-45s @%s' % (nm, pos))

# 2) 在名字之后找紧随的 python 源码（"from robodk.robolink import *" 或 "# -*- coding"）
print('\n=== 每个条目名之后第一个 python 源码块 ===')
for nm in names:
    p = found[nm]
    if p < 0:
        continue
    seg = d[p:p+4000]
    m = re.search(rb'# -\*- coding: utf-8 -\*-|from robodk\.robolink import \*|#!/usr/bin/env python3', seg)
    print('  %-45s 源码起点相对名字 +%s' % (nm, m.start() if m else None))

# 3) 用「代码块」定位法：先找所有 python 起点，再回头找最近的名字
py_starts = []
for m in re.finditer(rb'# -\*- coding: utf-8 -\*-\r?\n|#!/usr/bin/env python3\r?\n|from robodk\.robolink import \*', d):
    py_starts.append(m.start())
py_starts = sorted(set(py_starts))
print('\npython 候选起点数 =', len(py_starts))

def nearest_name(o):
    """在 o 之前 800 字节里找 UTF-16 名字。"""
    win = d[max(0, o-900):o]
    best = None
    for nm in names:
        b = nm.encode('utf-16-le')
        i = win.rfind(b)
        if i >= 0:
            if best is None or i > best[1]:
                best = (nm, i)
    return best[0] if best else None

print('\n=== 源码块归类 ===')
records = []
for o in py_starts:
    nm = nearest_name(o)
    # 代码终点：第一个 \x00
    z = d.find(b'\x00', o)
    # 但有些代码里没有 \x00；改用下一个 python 起点或 200KB 上限
    end = z if z > 0 else None
    # 选一个长度：优先到 \x00
    length = (end - o) if end else None
    records.append((o, nm, length))
for o, nm, ln in records:
    print('  @%-8d 名字=%-45s 长度=%s' % (o, nm, ln))
