#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行标零：POST /calibrate/home，并盯日志确认 servo calihome done，最后读数。
只发这一个厂商接口；不碰伺服固件、不改任何文件。"""
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


def api(cmd, wait=0.9):
    s = socket.create_connection((HOST, 30003), timeout=8)
    s.settimeout(6)
    s.sendall((cmd + '\n').encode())
    time.sleep(wait)
    d = s.recv(8192).decode('utf-8', 'replace')
    s.close()
    return d.strip().replace('\n', ' ')


print('=== 0) 标零前状态 ===')
print('  RobotMode :', api('RobotMode()'))
print('  GetAngle  :', api('GetAngle()'))
print('  最新三列  :')
print('   ', rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -2 | cut -c1-205" % D).strip()[:400])

print('')
print('=== 1) POST /calibrate/home ===')
try:
    req = urllib.request.Request('http://%s:22000/calibrate/home' % HOST, data=b'{}',
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=40) as r:
        print('  HTTP %s  %s' % (r.status, r.read().decode('utf-8', 'replace')[:120]))
except Exception as e:  # noqa: BLE001
    print('  调用异常: %s: %s' % (type(e).__name__, e))

print('')
print('=== 2) 等日志出现 HomeNumdone / servo calihome done（最多 40 秒）===')
ok = False
for i in range(20):
    time.sleep(2)
    out = rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -5 | cut -c1-150" % D)
    if 'servo calihome done' in out:
        print(out.strip())
        ok = True
        break
    if i % 3 == 0:
        print('   ... 第 %d 次检查' % (i + 1))
if not ok:
    print('  !! 40 秒内没看到 servo calihome done')
    print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -6 | cut -c1-150" % D).strip())

print('')
print('=== 3) 标零后读数 ===')
time.sleep(2)
print('  RobotMode :', api('RobotMode()'))
print('  GetAngle  :', api('GetAngle()'))
print('  最新三列  :')
print('   ', rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -3 | cut -c1-205" % D).strip()[:650])
print('')
print('  homeEncoder.json:')
print(rq("ls -la /dobot/userdata/project/settings/function/homeEncoder.json; grep -o '\"date\"[^,]*|\"time\"[^,]*' /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | tail -2" % ()).strip()[:300])
