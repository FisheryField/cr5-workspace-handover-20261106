#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把六轴归零：先读当前值；若已 ≈0 则只报告；否则 EnableRobot + JointMovJ(0×6) + Sync。
   基于之前用过的脚本序列（EnableRobot / SpeedFactor / JointMovJ / Sync），不额外加东西。"""
import re
import socket
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
PORT = 30003


def api(cmd, wait=1.0):
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
        s.settimeout(8)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % type(e).__name__


def angles():
    d = api('GetAngle()')
    m = re.search(r'\{([-0-9.eE,\s]+)\}', d)
    if not m:
        return None, d
    try:
        return [float(x) for x in m.group(1).split(',')][:6], d
    except ValueError:
        return None, d


def fmt(q):
    return ', '.join('%+.4f' % v for v in q) if q else 'N/A'


print('=== 1) 当前状态 ===')
print('  RobotMode :', api('RobotMode()'))
q, raw = angles()
print('  GetAngle  :', raw)
print('  解析六轴  :', fmt(q))
print('  GetErrorID:', api('GetErrorID()')[:110])

if q is None:
    print('')
    print('!! 读不到关节值（可能是控制模式不是 TCP）⇒ 请先在 HMI/DobotStudio 里切回 TCP 模式')
    sys.exit(1)

dmax = max(abs(v) for v in q)
print('')
print('  距零最大偏差 = %.4f°' % dmax)

if dmax <= 0.05:
    print('')
    print('★ 六轴已经在零位（偏差 ≤ 0.05°）⇒ 无需任何运动 ✓')
    sys.exit(0)

print('')
print('=== 2) 归零：SpeedFactor + EnableRobot + JointMovJ(0×6) + Sync ===')
print('  SpeedFactor(10) ->', api('SpeedFactor(10)'))
print('  EnableRobot     ->', api('EnableRobot()', wait=2.0))
time.sleep(1.0)
print('  RobotMode       ->', api('RobotMode()'))
print('  JointMovJ(0×6)  ->', api('JointMovJ(0.000000,0.000000,0.000000,0.000000,0.000000,0.000000)', wait=1.5))

print('')
print('=== 3) 等运动结束（最多 30 秒）===')
prev = None
for i in range(30):
    time.sleep(1)
    qq, _ = angles()
    if qq:
        dd = max(abs(v) for v in qq)
        print('   %2ds  %s   偏差 %.4f°' % (i + 1, fmt(qq), dd))
        if dd <= 0.05 and prev is not None and max(abs(a - b) for a, b in zip(qq, prev)) < 0.01:
            print('  ⇒ 已到位且静止 ✓')
            break
        prev = qq

print('')
print('=== 4) 结果 ===')
qq, raw = angles()
print('  GetAngle  :', raw)
print('  六轴      :', fmt(qq))
if qq:
    print('  距零最大偏差 = %.4f°' % max(abs(v) for v in qq))
print('  RobotMode :', api('RobotMode()'))
print('  报警      :', api('GetErrorID()')[:110])
