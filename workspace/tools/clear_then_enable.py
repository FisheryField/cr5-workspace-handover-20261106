#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清报警 -> SpeedFactor(5) -> EnableRobot -> 6 秒采样 -> DisableRobot。只做这一步，可中断。"""
import re
import socket
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'


def api(cmd, wait=0.9):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


def angles():
    d = api('GetAngle()')
    m = re.search(r'\{([-0-9.,\s]+)\}', d)
    return [float(x) for x in m.group(1).split(',')] if m else None


def fmt(q):
    return ', '.join('%+.4f' % v for v in q) if q else 'None'


print('=== 1) 清前 ===')
print('  RobotMode : %s' % api('RobotMode()'))
print('  ErrorID   : %s' % api('GetErrorID()'))
print('  姿态      : %s' % fmt(angles()))
print('')
print('=== 2) ClearError() ===')
print('  -> %s' % api('ClearError()', wait=1.5))
time.sleep(2.5)
print('  RobotMode : %s' % api('RobotMode()'))
print('  ErrorID   : %s' % api('GetErrorID()'))
print('')
print('=== 3) SpeedFactor(5) ===')
print('  -> %s' % api('SpeedFactor(5)'))
print('')
print('=== 4) EnableRobot() ===')
print('  -> %s' % api('EnableRobot()', wait=2.0))
q0 = angles()
print('  使能后立刻: %s' % fmt(q0))
print('')
print('=== 5) 采样 6 秒（每 0.5s）===')
prev = q0
for i in range(12):
    time.sleep(0.5)
    cur = angles()
    tag = ''
    if cur and prev:
        d = max(abs(a - b) for a, b in zip(cur, prev))
        if d > 0.05:
            tag = '   <== 变化 %.3f°' % d
    if i % 2 == 0 or tag:
        print('  %4.1fs  mode=%s  %s%s' % ((i + 1) * 0.5, api('RobotMode()').split('{')[-1].split('}')[0], fmt(cur), tag))
    prev = cur or prev
print('')
print('  报警     : %s' % api('GetErrorID()'))
print('')
print('=== 6) DisableRobot() ===')
print('  -> %s' % api('DisableRobot()', wait=1.5))
time.sleep(2)
print('  RobotMode : %s' % api('RobotMode()'))
print('  姿态      : %s' % fmt(angles()))
