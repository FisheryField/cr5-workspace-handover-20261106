#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C 方案可行性：同一时刻取
   主控 GetAngle()（当前 app=PDO补丁，读的是 0x6064 系）
   驱动器 0x6062 / 0x6063 / 0x6064（HTTP SDO 只读）
   判断：0x6062 与 0x6064 是否同系（决定撤补丁后主控与驱动器是否同系）"""
import json
import re
import socket
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]


def run(cmd, t=60):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def api(cmd, wait=0.9):
    s = socket.create_connection((HOST, 30003), timeout=8)
    s.settimeout(6)
    s.sendall((cmd + '\n').encode())
    time.sleep(wait)
    d = s.recv(8192).decode('utf-8', 'replace')
    s.close()
    return d.strip().replace('\n', ' ')


def get_angle():
    d = api('GetAngle()')
    m = re.search(r'\{([-0-9.,\s]+)\}', d)
    return [float(x) for x in m.group(1).split(',')] if m else [None] * 6


def sdo(axis, key, idx, slave):
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                 data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        return 'HTTPERR'
    time.sleep(0.9)
    txt = run("grep -a 'sdo read' %s | tail -3" % L)
    best = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == idx:
            v = int(float(m.group(4)))
            if 'fail' in line:
                return v
            best = v
    return best if best is not None else 'NOANS'


ang = get_angle()
print('主控 GetAngle() : %s' % ', '.join('%+.4f' % v if v is not None else '?' for v in ang))
print('')
print('%-4s | %12s | %12s | %12s | %12s | %s' % ('轴', '0x6062 给定', '0x6063 内部', '0x6064 实际', '主控 GetAngle', '0x6062 与 0x6064 差'))
print('-' * 92)
rows = []
for i, (axis, slave) in enumerate(AXES):
    v62 = sdo(axis, 'addr606200', 0x6062, slave)
    v63 = sdo(axis, 'addr606300', 0x6063, slave)
    v64 = sdo(axis, 'addr606400', 0x6064, slave)
    a = ang[i]
    d = (v62 - v64) if isinstance(v62, int) and isinstance(v64, int) else None
    rows.append((axis, v62, v63, v64, a, d))
    print('%-4s | %12s | %12s | %12s | %12s | %s'
          % (axis, v62, v63, v64, ('%+.4f' % a) if a is not None else '?',
             ('%d' % d) if d is not None else '-'))

print('')
vals62 = [r[1] for r in rows if isinstance(r[1], int)]
vals64 = [r[3] for r in rows if isinstance(r[3], int)]
if vals62 and vals64:
    same = all(a == b for a, b in zip(vals62, vals64))
    print('★ 判断：驱动器 0x6062 与 0x6064 是否逐轴相等 ⇒ %s' % ('相等（同系）✓' if same else '不相等（不同系）✗'))
    print('   逐轴差 : %s' % ', '.join(str(b - a) for a, b in zip(vals62, vals64)))
else:
    print('★ 读取不完整，无法判断（0x6062/0x6064 有 NOANS/HTTPERR）')
print('   注：这些是 16 位截断值，只能做"是否相等/趋势"判断，不能直接当角度用')
