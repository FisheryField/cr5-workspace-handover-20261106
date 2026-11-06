#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：六轴的 0x607D 软件位置限位 / 0x6098 回零方法 / 0x6060 模式 / 位置实际。
   全部只读。"""
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
SCALE = 360.0 / (20000.0 * 101.0)


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def read(idx, axis, slave, sub=0, signed=True):
    key = 'addr%04X%02X' % (idx, sub)
    body = {'body': [{'key': key, 'servoNum': axis}]}
    try:
        req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except Exception:  # noqa: BLE001
        return None
    time.sleep(0.85)
    txt = rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -4" % D)
    val = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == idx and int(m.group(3)) == sub:
            val = int(float(m.group(4)))
    if val is None:
        return None
    if signed and val >= (1 << 31):
        val -= (1 << 32)
    return val


AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
rows = [('0x607D:01 下限', 0x607D, 1), ('0x607D:02 上限', 0x607D, 2),
        ('0x6064 位置实际', 0x6064, 0), ('0x6098 回零方法', 0x6098, 0),
        ('0x6060 模式', 0x6060, 0)]

print('%-18s %-14s %-14s %-14s %-14s %-14s %-14s' % ('对象', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6'))
print('-' * 104)
for label, idx, sub in rows:
    cells = []
    for axis, slave in AXES:
        v = read(idx, axis, slave, sub)
        if v is None:
            cells.append('?')
        elif idx in (0x607D, 0x6064):
            cells.append('%d(%.2f°)' % (v, v * SCALE))
        else:
            cells.append(str(v))
    print('%-18s %-14s %-14s %-14s %-14s %-14s %-14s' % (label, *cells))
