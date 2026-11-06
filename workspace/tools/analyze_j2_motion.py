#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 mon2 日志：聚焦 J2 的"指令 vs 实际"，以及严格版两系差。"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
files = sorted(glob.glob(r'D:\mydata\workspace\mon2_*.log'), key=os.path.getmtime)
path = files[-1]
print('文件: %s (%.1f MB)' % (os.path.basename(path), os.path.getsize(path) / 1e6))

api, st, pt, cmds = [], [], [], []
for line in open(path, encoding='utf-8', errors='replace'):
    m = re.match(r'(\d\d:\d\d:\d\d) \[API\] (.*)', line)
    if m:
        t, r = m.group(1), m.group(2)
        mm = re.search(r'mode=(\S+)', r)
        am = re.search(r'ang=\{([-0-9.,\s]+)\}', r)
        try:
            a = [float(x) for x in am.group(1).split(',')] if am else None
        except ValueError:
            a = None
        api.append((t, mm.group(1) if mm else '?', a))
        continue
    m = re.match(r'(\d\d:\d\d:\d\d) \[STREAM\] mode=(\d+) q=([-+0-9.,]+)', line)
    if m:
        try:
            q = [float(x) for x in m.group(3).split(',')]
        except ValueError:
            continue
        st.append((m.group(1), int(m.group(2)), q))
        continue
    m = re.match(r'(\d\d:\d\d:\d\d) \[LOG\] (.*)', line)
    if m:
        t, r = m.group(1), m.group(2)
        if 'PoseTrace' in r:
            mm = re.search(r':\s*([-0-9.,\s]+)\s*$', r.strip())
            try:
                v = [float(x) for x in mm.group(1).strip().rstrip(',').split(',')] if mm else None
            except ValueError:
                v = None
            if v and len(v) >= 6:
                kind = ('next' if 'nextPos' in r else ('dem' if '0x6062' in r else 'act'))
                pt.append((t, kind, v))
        else:
            cmds.append((t, r.strip()[:190]))

print('API 样本 %d，STREAM 样本 %d，PoseTrace 行 %d，其它日志行 %d'
      % (len(api), len(st), len(pt), len(cmds)))

print('')
print('=== 运动指令 / 报警 / 使能（来自控制器日志）===')
for t, r in cmds:
    if re.search(r'recv =|queuedCmdIndex|AlarmSysSetBit|logServoError|robot enabled|robot disabled|gPowerDown|calihome', r):
        print('  %s  %s' % (t, r[:180]))

print('')
print('=== J2 三源轨迹（只打印变化点，阈值 0.05°）===')
print('  时间      |     API J2    |  STREAM J2   (mode) |   PoseTrace next / 0x6062 / gActual (J2)')
preva = prevs = None
pnext = pdem = pact = None
# 按时间归并
ev = []
for t, mode, a in api:
    ev.append((t, 0, (mode, a)))
for t, mode, q in st:
    ev.append((t, 1, (mode, q)))
for t, kind, v in pt:
    ev.append((t, 2, (kind, v)))
ev.sort(key=lambda x: x[0])
for t, k, payload in ev:
    if k == 0:
        mode, a = payload
        if a and (preva is None or abs(a[1] - preva) > 0.05 or mode != api[0][1]):
            print('  %s | %+11.4f | %s' % (t, a[1], ('mode=%s' % mode)))
            preva = a[1]
    elif k == 2:
        kind, v = payload
        j2 = v[1]
        if kind == 'next' and (pnext is None or abs(j2 - pnext) > 0.05):
            print('  %s |             |                     | next=%+9.4f' % (t, j2))
            pnext = j2
        elif kind == 'dem' and (pdem is None or abs(j2 - pdem) > 0.05):
            print('  %s |             |                     | 0x6062=%+8.4f' % (t, j2))
            pdem = j2
        elif kind == 'act' and (pact is None or abs(j2 - pact) > 0.05):
            print('  %s |             |                     | gActual=%+8.4f' % (t, j2))
            pact = j2

print('')
print('=== STREAM J2 的极值（看它到底走了多大）===')
vals = [q[1] for t, m, q in st]
if vals:
    print('  min = %+.4f   max = %+.4f   幅度 = %.4f' % (min(vals), max(vals), max(vals) - min(vals)))
print('=== API J2 的极值 ===')
av = [a[1] for t, m, a in api if a]
if av:
    print('  min = %+.4f   max = %+.4f   幅度 = %.4f' % (min(av), max(av), max(av) - min(av)))
print('=== PoseTrace 三列的 J2 极值 ===')
for kind in ('next', 'dem', 'act'):
    vs = [v[1] for t, k, v in pt if k == kind]
    if vs:
        print('  %-4s min = %+9.4f  max = %+9.4f  幅度 = %8.4f' % (kind, min(vs), max(vs), max(vs) - min(vs)))
