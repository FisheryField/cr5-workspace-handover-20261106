#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记录当前六轴完整基线（只读）：固件版本 + 三个独立来源的角度 + 状态。
输出到 J2_D8_observations.md（追加）。"""
import datetime
import json
import os
import re
import socket
import struct
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

lines = []


def emit(s):
    print(s, flush=True)
    lines.append(s)


def api(cmds):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        res = []
        for c in cmds:
            s.sendall((c + '\n').encode())
            time.sleep(0.4)
            try:
                res.append(s.recv(8192).decode('utf-8', 'replace').strip())
            except socket.timeout:
                res.append('<no reply>')
        s.close()
        return res
    except Exception:  # noqa: BLE001
        return None


def stream(port):
    try:
        s = socket.create_connection((HOST, port), timeout=6)
        s.settimeout(4)
        b = b''
        while len(b) < 400:
            b += s.recv(4096)
        s.close()
        for off in (176, 184, 192, 200, 208):
            v = struct.unpack_from('<6d', b, off)
            if all(abs(x) < 400 for x in v) and sum(1 for x in v if abs(x) > 0.05) >= 5:
                return v
    except Exception:  # noqa: BLE001
        return None
    return None


def version(slave):
    url = 'http://%s:22000/settings/readServoParams' % HOST
    body = {'body': [{'key': 'addr500007', 'servoNum': 'J%d' % (slave - 2)}]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception:  # noqa: BLE001
        return '?'
    time.sleep(0.5)
    try:
        out = subprocess.run([RSH, "grep -a 'readSDO' %s | tail -3" % LOG],
                             capture_output=True, text=True, timeout=40).stdout
    except Exception:  # noqa: BLE001
        return '?'
    for line in reversed(out.splitlines()):
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == 20480:
            return '0x%04X' % int(float(m.group(4)))
    return '?'


def pose_trace():
    try:
        out = subprocess.run([RSH, "grep -a 'PoseTrace' %s | tail -3" % LOG],
                             capture_output=True, text=True, timeout=40).stdout
    except Exception:  # noqa: BLE001
        return None
    vals = []
    for line in out.splitlines():
        if ':  ' in line:
            parts = line.split(':  ')[-1].split(',')
            if len(parts) >= 6:
                vals.append([p.strip() for p in parts[:6]])
    return vals if len(vals) == 3 else None


ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
emit('## 记录 %s' % ts)

a = api(['RobotMode()', 'GetAngle()', 'GetErrorID()'])
ang = a[1].split('{')[1].split('}')[0].split(',') if a and '{' in a[1] else None
emit('- `RobotMode()` = **%s**   `GetErrorID()` = %s' % (
    a[0].split('{')[1].split('}')[0] if a and '{' in a[0] else '?',
    (a[2].replace('\n', '').replace('\t', '') if a else '?')))
if ang:
    emit('- API `GetAngle()`            : %s' % ' '.join('%+10.5f' % float(x) for x in ang))
for port in (30004, 30005):
    v = stream(port)
    emit('- %d 反馈流                  : %s' % (port, ' '.join('%+10.5f' % x for x in v) if v else 'N/A'))
pt = pose_trace()
if pt:
    for tag, v in zip(('nextPos    ', '(PDO)      ', 'gActualPos '), pt):
        emit('- PoseTrace %s           : %s' % (tag, ' '.join('%+10.5f' % float(x) for x in v)))
emit('')
emit('| 轴 | slave | 固件版本字 `0x5000:07` |')
emit('|---|---|---|')
for axis, slave in AXES:
    emit('| %s | %d | **%s** |' % (axis, slave, version(slave)))
emit('')
emit('（`0x32D8` = 3.2.D.8，`0x3150` = 3.1.5.0）')
emit('')

with open(OUT, 'a', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('\n-> 追加写入 %s' % OUT)
