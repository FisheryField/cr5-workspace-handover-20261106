#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：查 J2 的位置相关对象，找那"一整圈"（360°）藏在哪个参数里。
   全部只读，不写。"""
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
SCALE = 360.0 / (20000.0 * 101.0)     # counts -> deg


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def read(idx, axis, slave, sub=0):
    key = 'addr%04X%02X' % (idx, sub)
    body = {'body': [{'key': key, 'servoNum': axis}]}
    try:
        req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        return None, 'HTTPERR %s' % type(e).__name__
    time.sleep(0.9)
    txt = rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -4" % D)
    val = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == idx:
            val = float(m.group(4))
    return val, None


OBJS = [
    (0x6064, 0, '位置实际值'),
    (0x6062, 0, '位置给定值'),
    (0x6063, 0, '内部单位实际'),
    (0x607A, 0, '目标位置'),
    (0x607C, 0, '★ 原点偏移 Home offset'),
    (0x607D, 1, '软件位置下限'),
    (0x607D, 2, '软件位置上限'),
    (0x6098, 0, '回零方法'),
    (0x6099, 1, '回零速度(开关)'),
    (0x6099, 2, '回零速度(零)'),
    (0x609A, 0, '回零加速度'),
    (0x6060, 0, '运行模式'),
    (0x6041, 0, '状态字'),
    (0x603F, 0, '故障码'),
]

print('%-28s %-8s %-14s %s' % ('对象', 'raw', '计数', '换算角度'))
print('-' * 74)
for idx, sub, label in OBJS:
    val, err = read(idx, 'J2', 4, sub)
    if err:
        print('%-28s %-8s %s' % ('0x%04X:%02X %s' % (idx, sub, label), '-', err))
        continue
    v = int(val) if val is not None else None
    if v is None:
        print('%-28s %-8s %s' % ('0x%04X:%02X %s' % (idx, sub, label), '-', 'NOANS'))
        continue
    # 以有符号 32 位看
    s = v - (1 << 32) if v >= (1 << 31) else v
    print('%-28s %-8d %-14d %+10.3f°' % ('0x%04X:%02X %s' % (idx, sub, label), v, s, s * SCALE))
