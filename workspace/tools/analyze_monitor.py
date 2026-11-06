#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 monitor_*.log：把 API 读数、30004 实际读数、两者差值的变化点抽出来。"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
files = sorted(glob.glob(r'D:\mydata\workspace\monitor_2026*.log'), key=os.path.getmtime)
path = files[-1]
print('分析文件: %s (%.1f KB)' % (os.path.basename(path), os.path.getsize(path) / 1024.0))

API = re.compile(r'\[API\] mode=(\S+) ang=\{(.*?)\}.*?err=(\S.*?)$')
STR = re.compile(r'\[STREAM\] mode=(\d+) q=([-+0-9.,]+) v=([-+0-9.,]+)')
NAMES = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']

api_hist = []      # (t, mode, [6], err)
str_hist = []      # (t, mode, [6], maxv)
for line in open(path, encoding='utf-8', errors='replace'):
    m = re.match(r'(\d\d:\d\d:\d\d) \[API\] (.*)', line)
    if m:
        t, rest = m.group(1), m.group(2)
        mm = re.search(r'mode=(\S+)', rest)
        am = re.search(r'ang=\{(.*?)\}', rest)
        em = re.search(r'err=(.*)$', rest)
        mode = mm.group(1) if mm else '?'
        try:
            ang = [float(x) for x in am.group(1).split(',')] if am else None
        except ValueError:
            ang = None
        api_hist.append((t, mode, ang, (em.group(1)[:60] if em else '')))
        continue
    m = re.match(r'(\d\d:\d\d:\d\d) \[STREAM\] (.*)', line)
    if m:
        t, rest = m.group(1), m.group(2)
        qm = re.search(r'q=([-+0-9.,]+)', rest)
        vm = re.search(r'v=([-+0-9.,]+)', rest)
        try:
            q = [float(x) for x in qm.group(1).split(',')] if qm else None
            v = [float(x) for x in vm.group(1).split(',')] if vm else []
        except ValueError:
            q, v = None, []
        str_hist.append((t, q, max(abs(x) for x in v) if v else 0.0))

print('API 样本 %d 条，STREAM 样本 %d 条' % (len(api_hist), len(str_hist)))

print('')
print('=== API GetAngle 的变化点（主控系的运动）===')
prev = None
for t, mode, ang, err in api_hist:
    if ang is None:
        continue
    if prev is None or max(abs(a - b) for a, b in zip(ang, prev)) > 0.05:
        print('  %s mode=%s  %s%s' % (t, mode, ', '.join('%+.4f' % x for x in ang),
                                      ('   err=%s' % err) if err and 'EXC' in err else ''))
        prev = ang

print('')
print('=== STREAM qActual 的变化点（驱动器的运动）===')
prev = None
for t, q, mv in str_hist:
    if q is None:
        continue
    if prev is None or max(abs(a - b) for a, b in zip(q, prev)) > 0.1:
        print('  %s  %s   (max|v|=%.2f)' % (t, ', '.join('%+.4f' % x for x in q), mv))
        prev = q

print('')
print('=== 同一时刻的"两系差"（API − STREAM，取每个 API 样本前最近一条 STREAM）===')
import bisect
stimes = [s[0] for s in str_hist]
shown = 0
prev_d = None
for t, mode, ang, err in api_hist:
    if ang is None:
        continue
    i = bisect.bisect_right(stimes, t) - 1
    if i < 0:
        continue
    q = str_hist[i][1]
    if q is None:
        continue
    d = [a - b for a, b in zip(ang, q)]
    if prev_d is None or max(abs(x - y) for x, y in zip(d, prev_d)) > 0.05:
        print('  %s mode=%s  Δ = %s' % (t, mode, ', '.join('%+8.4f' % x for x in d)))
        prev_d = d
        shown += 1
print('  （共 %d 个差异变化点）' % shown)

print('')
print('=== mode 变化与错误 ===')
prevm = None
for t, mode, ang, err in api_hist:
    if mode != prevm:
        print('  %s mode %s -> %s   err=%s' % (t, prevm, mode, err[:70]))
        prevm = mode
    if err and ('EXC' in err or ('[' in err and re.search(r'\d', err))):
        print('  %s !! err=%s' % (t, err[:80]))
