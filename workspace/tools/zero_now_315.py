#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标零前确认 + 发标零 + 盯日志。
   ① SDO 读六轴 0x603F（故障码，应全 0）
   ② SDO 读六轴 0x6064（位置实际，看原始/定基）
   ③ 发 POST /calibrate/home
   ④ 盯 HomeNumdone 0→2→4→6 + servo calihome done
"""
import json
import re
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


def sdo_read(idx, sub, axis, slave):
    key = 'addr%04X%02X' % (idx, sub)
    body = {'body': [{'key': key, 'servoNum': axis}]}
    try:
        req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        return 'ERR:%s' % type(e).__name__
    time.sleep(0.9)
    txt = rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -4" % D)
    val = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == idx and int(m.group(3)) == sub:
            val = float(m.group(4))
    return val


AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
SCALE = 360.0 / (20000.0 * 101.0)

print('=== 1) 六轴 0x603F 故障码（应全 0）===')
bad = []
for ax, sl in AXES:
    v = sdo_read(0x603F, 0, ax, sl)
    i = int(v) if isinstance(v, float) else None
    if i:
        bad.append((ax, i))
    print('  %-3s 0x603F = %s' % (ax, i if i is not None else v))
print('  ⇒ %s' % ('全部为 0 ✓ 可以标零' if not bad else '★ 仍有故障: %s ✗（需先清，标零会被拦）' % bad))

print('')
print('=== 2) 六轴 0x6064 位置实际（原始/定基对照）===')
for ax, sl in AXES:
    v = sdo_read(0x6064, 0, ax, sl)
    print('  %-3s = %-12s (%.2f°)' % (ax, int(v) if isinstance(v, float) else v,
                                      (v or 0) * SCALE))

if bad:
    print('')
    print('!! 有故障码，未发标零。请先在示教器清报警/整柜断电，再跑本脚本。')
    sys.exit(1)

print('')
print('=== 3) POST /calibrate/home ===')
try:
    req = urllib.request.Request('http://%s:22000/calibrate/home' % HOST, data=b'{}',
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=40) as r:
        print('  HTTP %s  %s' % (r.status, r.read().decode('utf-8', 'replace')[:120]))
except Exception as e:  # noqa: BLE001
    print('  异常: %s: %s' % (type(e).__name__, e))

print('')
print('=== 4) 盯 HomeNumdone（最多 40 秒）===')
done = False
for i in range(20):
    time.sleep(2)
    out = rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -5 | cut -c1-150" % D)
    if 'servo calihome done' in out:
        print('  ★ 成功（第 %d 秒）:' % (i * 2 + 2))
        print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -9 | cut -c1-150" % D).rstrip())
        done = True
        break
    if i % 4 == 0:
        print('   ... %d/20' % (i + 1))
if not done:
    print('  ✗ 未见 done；最近记录：')
    print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -9 | cut -c1-150" % D).rstrip())

print('')
print('=== 5) 标零后六轴三列 ===')
print(rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -3 | cut -c1-205" % D).rstrip())
print('')
print('=== 6) 标零后 0x603F ===')
for ax, sl in AXES:
    v = sdo_read(0x603F, 0, ax, sl)
    print('  %-3s = %s' % (ax, int(v) if isinstance(v, float) else v))
