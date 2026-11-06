#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归零（带运动/报警监控与自动中止）：
   ClearError -> SpeedFactor(5) -> EnableRobot -> 监控3s -> POST /calibrate/home
   -> 观察 HomeNumdone/servo calihome done -> 读姿态与 homeEncoder -> DisableRobot
   任何异常（运动>2° 或出现报警）立即中止并下使能。"""
import re
import socket
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'


def api(cmd, wait=0.9, timeout=8):
    try:
        s = socket.create_connection((HOST, 30003), timeout=timeout)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


def post(path, body='{}'):
    req = urllib.request.Request('http://%s:22000%s' % (HOST, path), data=body.encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:100]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:100]


def angles():
    d = api('GetAngle()')
    m = re.search(r'\{([-0-9.,\s]+)\}', d)
    return [float(x) for x in m.group(1).split(',')] if m else None


def mode():
    d = api('RobotMode()')
    m = re.search(r'\{(\d+)\}', d)
    return int(m.group(1)) if m else None


def errs():
    return api('GetErrorID()').replace('\t', ' ').replace('\n', ' ')


def fmt(q):
    return ', '.join('%+.4f' % v for v in q) if q else 'None（读不到）'


q0 = angles()
print('=== 归零前 ===')
print('  mode  : %s' % mode())
print('  报警  : %s' % errs()[:110])
print('  姿态  : %s' % fmt(q0))
print('')
print('=== ClearError ===')
print('  -> %s' % api('ClearError()', wait=1.5))
time.sleep(2)
print('  mode=%s  报警=%s' % (mode(), errs()[:90]))
print('')
print('=== SpeedFactor(5) + EnableRobot ===')
print('  SpeedFactor -> %s' % api('SpeedFactor(5)'))
print('  EnableRobot -> %s' % api('EnableRobot()', wait=2.0))
prev = q0
abort = None
for i in range(6):
    time.sleep(0.5)
    cur = angles()
    m = mode()
    if cur and prev:
        dmax = max(abs(a - b) for a, b in zip(cur, prev))
        if dmax > 2.0:
            abort = '使能后手臂移动 %.3f°（第 %.1fs）' % (dmax, (i + 1) * 0.5)
            break
    if m == 9:
        abort = '进入 mode 9（错误态）'
        break
    prev = cur or prev
print('  监控结果: %s' % (abort if abort else '未检测到运动/错误 ✓'))
print('  mode=%s' % mode())
if abort:
    print('')
    print('!! 已中止，不执行标零。下使能保护：')
    print('  DisableRobot -> %s' % api('DisableRobot()', wait=1.5))
    print('  报警: %s' % errs()[:110])
    sys.exit(3)

print('')
print('=== POST /calibrate/home ===')
print('  -> %s' % (post('/calibrate/home'),))
done = False
for i in range(16):
    time.sleep(1.5)
    st = api('RobotMode()')
    if i % 3 == 0:
        print('  %4.1fs  mode=%s  姿态=%s' % ((i + 1) * 1.5, st, fmt(angles())))
    if re.search(r'\{(\d+)\}', st) and int(re.search(r'\{(\d+)\}', st).group(1)) == 9:
        print('  !! 出现错误态')
        break
print('')
print('=== 归零后 ===')
print('  姿态  : %s' % fmt(angles()))
print('  报警  : %s' % errs()[:110])
print('')
print('=== 下使能 ===')
print('  -> %s' % api('DisableRobot()', wait=1.5))
time.sleep(2)
print('  最终姿态: %s' % fmt(angles()))
print('  mode=%s' % mode())
