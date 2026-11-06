#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：逐轴读厂商参数（HTTP SDO 通道，值在日志 readSDO 行）。
   稳健解析：请求后取日志尾部，优先匹配 'sdo read fail' 行（该行的 value= 才是读回值）。"""
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
AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
# key 格式 = addr + 4位index + 2位sub；厂商参数 H<组>.<序号> → 0x20<组>:<序号+1>
PARAMS = [
    ('H01.17 编码器位置角(°)', 'addr200112', 0x2001),   # sub 0x12 = 18 = 17+1
    ('H0C.02 编码器校零使能', 'addr200c03', 0x200C),    # sub 3 = 2+1
    ('H01.18 校零电流(%)', 'addr200113', 0x2001),       # sub 0x13 = 19
    ('H0C.00 故障复位', 'addr200c01', 0x200C),          # sub 1 = 0+1
    ('H01.14 单圈分辨率', 'addr20010f', 0x2001),        # sub 0x0f = 15
    ('版本字 0x5000:07', 'addr500007', 0x5000),
]
out = []


def emit(s):
    print(s, flush=True)
    out.append(s)


def run(cmd, t=45):
    try:
        return subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                              stdin=subprocess.DEVNULL).stdout
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


def read(axis, key, index, slave):
    url = 'http://%s:22000/settings/readServoParams' % HOST
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception:  # noqa: BLE001
        return None
    time.sleep(0.7)
    txt = run("grep -a 'readSDO' %s | tail -4" % LOG)
    best = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if not m:
            continue
        if int(m.group(1)) == slave and int(m.group(2)) == index:
            v = float(m.group(4))
            if 'fail' in line:          # 权威行
                return v
            best = v
    return best


emit('## 厂商参数逐轴实测（%s）' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
emit('')
hdr = '| 轴 | slave | ' + ' | '.join(n for n, _, _ in PARAMS) + ' |'
emit(hdr)
emit('|---|' + '---|' * (len(PARAMS) + 1))
for axis, slave in AXES:
    cells = []
    for name, key, index in PARAMS:
        v = read(axis, key, index, slave)
        if v is None:
            cells.append('?')
        elif '版本字' in name:
            cells.append('0x%04X' % int(v))
        else:
            cells.append('%g' % v)
    emit('| %s | %d | %s |' % (axis, slave, ' | '.join(cells)))
emit('')
with open(OUT, 'a', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
print('-> 追加写入 %s' % OUT)
