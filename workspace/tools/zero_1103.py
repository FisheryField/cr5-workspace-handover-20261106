#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标零（2026-11-03，3.1.5.0 + 原版 + 已使能）。
   先记录基线，再 POST /calibrate/home，盯 HomeNumdone 0→2→4→6 + servo calihome done。"""
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
                       encoding='utf-8', errors='replace', stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


print('=== 0) 标零前基线 ===')
print('  固件 :', rq("grep -a 'settVersion' %s/log 2>/dev/null | tail -14 | grep -a 'servo1 ' | tail -1 | cut -c1-100" % D).strip())
print('  主控 :', rq("md5sum /dobot/userdata/codesys/allST/Application.app").strip())
print('  使能 :', rq("grep -a 'robot enabled\\|robot disabled' %s/log 2>/dev/null | tail -1 | cut -c1-120" % D).strip())
print('  六轴 :', rq("grep -a 'PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -1 | cut -c1-205" % D).strip())

print('')
print('=== 1) POST /calibrate/home ===')
t0 = time.time()
try:
    req = urllib.request.Request('http://%s:22000/calibrate/home' % HOST, data=b'{}',
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=40) as r:
        print('  HTTP %s  %s  (%.1fs)' % (r.status, r.read().decode('utf-8', 'replace')[:120],
                                          time.time() - t0))
except Exception as e:  # noqa: BLE001
    print('  异常: %s: %s' % (type(e).__name__, e))

print('')
print('=== 2) 盯 HomeNumdone（最多 60 秒）===')
done = False
for i in range(30):
    time.sleep(2)
    out = rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -6 | cut -c1-150" % D)
    if 'servo calihome done' in out:
        print('  ★ 成功（第 %d 秒）:' % (i * 2 + 2))
        print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -10 | cut -c1-150" % D).rstrip())
        done = True
        break
    if i % 3 == 0:
        print('   ... %ds' % (i * 2 + 2))

if not done:
    print('  ✗ 未见 done；最近记录：')
    print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -10 | cut -c1-150" % D).rstrip())

print('')
print('=== 3) 标零后六轴三列 ===')
print(rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -3 | cut -c1-205" % D).rstrip())

print('')
print('=== 4) 标零后报警 / 故障 ===')
print(rq("grep -a 'AlarmSysSetBit' %s/log 2>/dev/null | tail -6 | cut -c1-115" % D).rstrip())
print(rq("grep -a 'logServoError' %s/log 2>/dev/null | tail -4 | cut -c1-140" % D).rstrip())

print('')
print('=== 5) homeEncoder.json 时间戳 ===')
print(rq("ls -la /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json; grep -o '\"time\": \"[^\"]*\"' /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json 2>/dev/null | tail -3").rstrip())
