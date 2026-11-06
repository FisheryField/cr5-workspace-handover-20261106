#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐轴读驱动器对象（只读，厂商 HTTP SDO 通道；值在日志 readSDO 行）。
用于 A/B 对照：J2=D8 vs 其余=3.1.5.0。
读：0x6064 位置实际值、0x2001:18 编码器位置角(H01.17)、0x2001:19 编码器校零电流(H01.18)、
    0x200C:02 编码器校零使能(H0C.02)、0x200C:01 故障复位(H0C.00)
用法：python tools/read_servo_objects.py "标签"
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'J2_D8_observations.md')
SCALE = 360.0 / (20000 * 101)
AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
OBJS = [('0x6064位置实际', 'addr606400', 24676),
        ('0x2001:18编码器位置角', 'addr200118', 8193),
        ('0x2001:19编码器校零电流', 'addr200119', 8193),
        ('0x200C:02编码器校零使能', 'addr200c02', 8204),
        ('0x200C:01故障复位', 'addr200c01', 8204)]
tag = sys.argv[1] if len(sys.argv) > 1 else ''
lines = []


def emit(s):
    print(s, flush=True)
    lines.append(s)


def read_one(axis, key, index, sub=0):
    url = 'http://%s:22000/settings/readServoParams' % HOST
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception:  # noqa: BLE001
        return None
    time.sleep(0.5)
    try:
        out = subprocess.run([RSH, "grep -a 'readSDO' %s | tail -3" % LOG],
                             capture_output=True, text=True, timeout=40).stdout
    except Exception:  # noqa: BLE001
        return None
    for line in reversed(out.splitlines()):
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(2)) == index:
            return float(m.group(4))
    return None


emit('## %s（%s）' % (tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
emit('')
emit('| 轴 | 固件 | ' + ' | '.join(n for n, _, _ in OBJS) + ' |')
emit('|---|' + '---|' * (len(OBJS) + 1))
for axis, slave in AXES:
    fw = '3.2.D.8' if axis == 'J2' else '3.1.5.0'
    cells = []
    for name, key, index in OBJS:
        v = read_one(axis, key, index)
        if v is None:
            cells.append('?')
        elif '位置实际' in name:
            cells.append('%d (%.4f°)' % (int(v), v * SCALE))
        else:
            cells.append('%g' % v)
    emit('| %s | %s | %s |' % (axis, fw, ' | '.join(cells)))
emit('')
with open(OUT, 'a', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('-> 追加写入 %s' % OUT)
