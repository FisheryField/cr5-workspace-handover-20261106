#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读六轴的 H0B.12 / H0B.13 / H0A.08 / H01.17 与 0x6064 / 0x603F / 0x607D。
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


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def read(idx, sub, axis, slave):
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
            val = float(m.group(4))
    if val is None:
        return None
    v = int(val)
    if v >= (1 << 31):
        v -= (1 << 32)
    return v


AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
ROWS = [
    ('H0B.12 CSP增量阈值', 0x200B, 12),
    ('H0B.13 CSP增量次数', 0x200B, 13),
    ('H0A.08 跟踪误差阈值', 0x200A, 8),
    ('H0A.09 滤波时间', 0x200A, 9),
    ('H01.17 编码器位置角', 0x2001, 17),
    ('0x6064 位置实际', 0x6064, 0),
    ('0x603F 故障码', 0x603F, 0),
    ('0x607D:02 上限', 0x607D, 2),
]
print('%-20s %-9s %-9s %-9s %-9s %-9s %-9s' % ('参数', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6'))
print('-' * 82)
for label, idx, sub in ROWS:
    cells = []
    for axis, slave in AXES:
        v = read(idx, sub, axis, slave)
        cells.append('?' if v is None else str(v))
    print('%-20s %-9s %-9s %-9s %-9s %-9s %-9s' % (label, *cells))
