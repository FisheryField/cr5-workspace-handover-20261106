#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使能 + 标零 + 盯日志（原版已就位，本次是"再来一遍标零"）。"""
import re
import socket
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = [r'C:\Program Files\PyManager\python.exe', r'D:\mydata\workspace\tools\rssh.py']
D = '/dobot/userdata/CR5_sys_files/project/logs/all'


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def api(cmd, wait=1.2):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(8)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s: %s' % (type(e).__name__, e)


print('=== 0) 标零前 ===')
print('  当前 app :', rq("md5sum /dobot/userdata/codesys/allST/Application.app").strip())
print('  RobotMode :', api('RobotMode()'))
print('  GetAngle  :', api('GetAngle()'))
print('  GetErrorID:', api('GetErrorID()')[:120])

print('')
print('=== 1) ClearError + EnableRobot ===')
print('  ClearError  :', api('ClearError()', wait=1.5))
time.sleep(1.5)
print('  EnableRobot :', api('EnableRobot()', wait=2.0))
time.sleep(1.0)
print('  RobotMode   :', api('RobotMode()'))

print('')
print('=== 2) POST /calibrate/home ===')
try:
    req = urllib.request.Request('http://%s:22000/calibrate/home' % HOST, data=b'{}',
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=40) as r:
        print('  HTTP %s  %s' % (r.status, r.read().decode('utf-8', 'replace')[:120]))
except Exception as e:  # noqa: BLE001
    print('  异常: %s: %s' % (type(e).__name__, e))

print('')
print('=== 3) 等 servo calihome done（最多 40 秒）===')
done = False
for i in range(20):
    time.sleep(2)
    out = rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -5 | cut -c1-150" % D)
    if 'servo calihome done' in out:
        print('  ★ 成功（第 %d 秒）：' % (i * 2 + 2))
        print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -8 | cut -c1-150" % D).strip())
        done = True
        break
    if i % 4 == 0:
        print('   ... %d/20' % (i + 1))
if not done:
    print('  ✗ 未见 done；最近记录：')
    print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -8 | cut -c1-150" % D).strip())

print('')
print('=== 4) 标零后六轴 ===')
print('  GetAngle :', api('GetAngle()'))
print(' ', rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -2 | cut -c1-205" % D).strip()[:420])
print('')
print('  驱动器故障码:')
print(rq("grep -a 'logServoError' %s/log 2>/dev/null | tail -3 | cut -c1-140" % D).strip())
