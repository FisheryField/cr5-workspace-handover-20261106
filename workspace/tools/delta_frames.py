#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从日志里抽取"同一时刻"的 PoseTrace 三元组，计算
   Δ = (PDO0x6062 定基系) − (gActualPosition 驱动器系)
   看 Δ 是否恒定（恒定 ⇒ 可用常值补偿；不恒定 ⇒ 另有机制）"""
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
NAMES = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']


def run(cmd, t=90):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or ''))


# 抓最近 60 组三元组（每组三行：nextPos / 0x6062 / gActualPosition）
out = run("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' "
          "%s | tail -120 | cut -c1-220" % L)
lines = [l for l in out.splitlines() if 'PoseTrace' in l]


def nums(line):
    m = re.search(r':\s*([-0-9.,\s]+)$', line.strip())
    if not m:
        return None
    try:
        return [float(x) for x in m.group(1).strip().rstrip(',').split(',')]
    except ValueError:
        return None


triples = []
buf = {}
for l in lines:
    if 'nextPos' in l:
        buf = {'next': nums(l)}
    elif '0x6062' in l:
        buf['dem'] = nums(l)
    elif 'gActualPosition' in l:
        buf['act'] = nums(l)
        if all(k in buf for k in ('next', 'dem', 'act')) and all(buf[k] for k in buf):
            triples.append(dict(buf))

print('抽到 %d 组完整三元组' % len(triples))
print('')
if not triples:
    print('（不足，无法比较）')
    sys.exit(0)

print('%-3s | %14s | %14s | %14s | %14s' % ('轴', 'nextPos', '0x6062', 'gActualPosition', 'Δ(6062−actual)'))
print('-' * 88)
last = triples[-1]
for i, n in enumerate(NAMES):
    print('%-3s | %+14.6f | %+14.6f | %+14.6f | %+14.6f'
          % (n, last['next'][i], last['dem'][i], last['act'][i], last['dem'][i] - last['act'][i]))

print('')
print('=== Δ 在多组之间的稳定性（每组算 Δ，取最大最小）===')
for i, n in enumerate(NAMES):
    ds = [t['dem'][i] - t['act'][i] for t in triples]
    print('  %s : Δ min %+10.4f  max %+10.4f  跨度 %8.4f  %s'
          % (n, min(ds), max(ds), max(ds) - min(ds),
             '恒定' if max(ds) - min(ds) < 0.05 else '变化 ✗'))

print('')
print('=== nextPos 与 0x6062 的关系（两者是否恒等）===')
for i, n in enumerate(NAMES):
    ds = [t['next'][i] - t['dem'][i] for t in triples]
    print('  %s : next−dem 跨度 %8.4f  %s' % (n, max(ds) - min(ds), '一致' if max(ds) - min(ds) < 0.05 else '不一致 ✗'))
