#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使能 + 标零：EnableRobot -> POST /calibrate/home -> 盯 servo calihome done -> 读数。
   只调用厂商接口；不改固件、不改文件。"""
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


def api(cmd, wait=1.0):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(8)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % type(e).__name__


print('=== 0) 标零前 ===')
print('  RobotMode :', api('RobotMode()'))
print('  GetAngle  :', api('GetAngle()'))
print('  GetErrorID:', api('GetErrorID()')[:110])

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
print('=== 3) 等 servo calihome done（最多 60 秒）===')
done = False
for i in range(30):
    time.sleep(2)
    out = rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -4 | cut -c1-150" % D)
    if 'servo calihome done' in out:
        print('  ★ 成功：')
        print(out.strip())
        done = True
        break
    if i % 5 == 0:
        print('   ... %d/30' % (i + 1))
if not done:
    print('  !! 未见 done；最近记录：')
    print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -5 | cut -c1-150" % D).strip())

print('')
print('=== 4) 标零后读数 ===')
time.sleep(2)
print('  RobotMode :', api('RobotMode()'))
print('  GetAngle  :', api('GetAngle()'))
print('  最新三列  :')
print('   ', rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -3 | cut -c1-205" % D).strip()[:650])
print('')
print('=== 5) 零位持久化记录 ===')
print(rq("ls -la /dobot/userdata/project/settings/function/homeEncoder.json; grep -o '\"date\"[^,]*' /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | tail -2; grep -A8 innerEncoder /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | head -9").strip()[:400])
