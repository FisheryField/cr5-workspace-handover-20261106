#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：逐轴读 H01.17(编码器位置角) / H01.18 / H0C.02 与 0x6064 位置实际。
   全部只读，不写任何参数。"""
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


def read(key, axis, slave):
    body = {'body': [{'key': key, 'servoNum': axis}]}
    try:
        req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        return 'HTTPERR(%s)' % type(e).__name__
    time.sleep(0.9)
    txt = rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -4" % D)
    val = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave:
            if 'fail' in line:
                val = m.group(4)
    return val if val is not None else 'NOANS'


AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
KEYS = [('H01.17 编码器位置角', '200112'), ('H01.18 校零电流', '200113'),
        ('H0C.02 校零使能', '200C03'), ('0x6064 位置实际', 'addr606400')]

print('%-22s %-10s %-10s %-10s %-10s %-10s %-10s' % ('参数', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6'))
print('-' * 84)
for label, key in KEYS:
    row = []
    for axis, slave in AXES:
        row.append(read(key, axis, slave))
    print('%-22s %-10s %-10s %-10s %-10s %-10s %-10s' % (label, *row))
