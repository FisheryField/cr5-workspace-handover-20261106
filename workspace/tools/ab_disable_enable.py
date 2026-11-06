#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B 实验：自己做一次 Disable -> Enable，逐轴对比"主控上报的关节角"。
   J2 = 3.2.D.8，其余五轴 = 3.1.5.0。全程只读 + 两次状态切换命令。"""
import datetime
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'J2_D8_observations.md')
AXES = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']
out_lines = []


def emit(s):
    print(s, flush=True)
    out_lines.append(s)


def api(cmds, wait=0.7):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        res = []
        for c in cmds:
            s.sendall((c + '\n').encode())
            time.sleep(wait)
            try:
                res.append(s.recv(16384).decode('utf-8', 'replace').strip())
            except socket.timeout:
                res.append('<no reply>')
        s.close()
        return res
    except Exception as e:  # noqa: BLE001
        return ['EXC %s' % e]


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
                if abs(v[0]) < 1e-9:
                    return v[1:]
                return v
    except Exception:  # noqa: BLE001
        return None
    return None


def snap(label):
    a = api(['RobotMode()', 'GetAngle()', 'GetErrorID()'])
    mode = a[0].split('{')[1].split('}')[0] if '{' in a[0] else '?'
    ang = None
    try:
        ang = [float(x) for x in a[1].split('{')[1].split('}')[0].split(',')]
    except Exception:  # noqa: BLE001
        pass
    st = stream(30004)
    err = a[2].replace('\n', '').replace('\t', '')
    err = err.split('{', 1)[1].split('}', 1)[0] if '{' in err else err
    emit('### %s   (%s)' % (label, datetime.datetime.now().strftime('%H:%M:%S')))
    emit('- mode=**%s**   errors=%s' % (mode, err))
    if ang:
        emit('- `GetAngle()`  : ' + ' '.join('%+9.4f' % x for x in ang))
    if st:
        emit('- 30004 反馈流   : ' + ' '.join('%+9.4f' % x for x in st))
    emit('')
    return ang, st, mode


emit('## A/B 实验：Disable → Enable（%s）' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
emit('')
emit('J2 = 3.2.D.8；J1/J3/J4/J5/J6 = 3.1.5.0')
emit('')

before, before_st, _ = snap('① 切换前（使能中）')
emit('>>> 发送 DisableRobot()')
r = api(['DisableRobot()'], wait=2.0)
emit('- 返回: %s' % r[0].replace('\n', ' '))
time.sleep(3)
mid, mid_st, mode_mid = snap('② 下使能中（3 秒后）')

emit('>>> 发送 EnableRobot()')
r = api(['EnableRobot()'], wait=8.0)
emit('- 返回: %s' % r[0].replace('\n', ' '))
time.sleep(6)
after, after_st, mode_after = snap('③ 上使能后（6 秒后）')

emit('### 逐轴对比（主控上报角，单位°）')
emit('')
emit('| 轴 | 固件 | ① 切换前 | ② 下使能中 | ③ 上使能后 | ②−① | ③−② | 判定 |')
emit('|---|---|---|---|---|---|---|---|')
for i, ax in enumerate(AXES):
    fw = '**3.2.D.8**' if ax == 'J2' else '3.1.5.0'
    if not (before and mid and after):
        emit('| %s | %s | ? | ? | ? | | | 数据缺失 |' % (ax, fw))
        continue
    d1 = mid[i] - before[i]
    d2 = after[i] - mid[i]
    tot = after[i] - before[i]
    verdict = '**未变 ✓**' if abs(tot) < 0.3 else '**变了 %+.2f° ✗**' % tot
    emit('| %s | %s | %+9.4f | %+9.4f | %+9.4f | %+.3f | %+.3f | %s |'
         % (ax, fw, before[i], mid[i], after[i], d1, d2, verdict))
emit('')

# 日志里的报警/伺服码
try:
    lg = subprocess.run([RSH, "grep -a 'AlarmSysSetBit\\|logServoError' %s | tail -12" % LOG],
                        capture_output=True, text=True, timeout=40).stdout
except Exception:  # noqa: BLE001
    lg = ''
emit('### 本次切换期间的报警/伺服码（日志尾部）')
emit('```')
for line in lg.strip().splitlines()[-10:]:
    emit(line.strip()[:150])
emit('```')
emit('')
with open(OUT, 'a', encoding='utf-8') as f:
    f.write('\n'.join(out_lines) + '\n')
print('\n-> 追加写入 %s' % OUT)
