#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B 判读：最后一次急停(0x74/handleEmergency)之前的姿态 vs 现在的实时姿态。
   看哪些轴落到了各自的"原始计数帧"（=丢定基），J2 应例外（已刷 3.2.D.8）。"""
import datetime
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
RAW = [8.35, 12.84, -3.35, 21.10, 15.91, 19.72]     # 原始计数帧（3.1.5.0 丢定基时落到这里）
FW = ['3.1.5.0', '**3.2.D.8**', '3.1.5.0', '3.1.5.0', '3.1.5.0', '3.1.5.0']
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


def api(cmd, wait=0.9):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace').strip()
        s.close()
        return d
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


def stream(port=30004):
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
                return v[1:] if abs(v[0]) < 1e-9 else v
    except Exception:  # noqa: BLE001
        return None
    return None


# 1) 最后一次急停的时间
ev = run("grep -an 'handleEmergency' %s | tail -4" % LOG)
stop_ts = None
for line in ev.splitlines():
    m = re.search(r'\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)', line)
    if m and '0->1' in line:
        stop_ts = m.group(1)
emit('## A/B 判读（急停前后）  %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
emit('')
emit('最后一次急停（handleEmergency 0->1）时间：**%s**' % stop_ts)
emit('')

# 2) 急停前最后一套 PoseTrace
pre = run("awk -v T='%s' '/^\\[20/ {ts=substr($0,2,19)} /PoseTrace: gRobotAxisMove.nextPos|PoseTrace: \\(PDO|PoseTrace: gActualPosition/ {if (ts<=T) print ts\" \"$0}' %s | tail -3"
          % (stop_ts or '9999', LOG))
pre_vals = None
for line in pre.splitlines():
    if ':  ' in line:
        v = [float(x) for x in line.split(':  ')[-1].split(',')[:6]]
        if 'gActualPosition' in line:
            pre_vals = v
emit('急停前（日志最后一套 PoseTrace / gActualPosition）：')
emit('```')
emit(pre.strip() or '(无)')
emit('```')
emit('')

# 3) 现在的实时值
mode = api('RobotMode()')
ang_s = api('GetAngle()')
err = api('GetErrorID()')
now = None
try:
    now = [float(x) for x in ang_s.split('{')[1].split('}')[0].split(',')]
except Exception:  # noqa: BLE001
    pass
st = stream()
emit('- 现在 `RobotMode()` = %s' % mode.split('{')[1].split('}')[0] if '{' in mode else mode)
emit('- 现在 `GetErrorID()` = %s' % err.replace('\n', '').replace('\t', '')[:90])
if now:
    emit('- 现在 `GetAngle()`  = ' + ' '.join('%+9.4f' % x for x in now))
if st:
    emit('- 现在 30004 反馈流 = ' + ' '.join('%+9.4f' % x for x in st))
emit('')

# 4) 对照表
emit('| 轴 | 固件 | 急停前 | 现在 | Δ | 是否落到原始帧 | 判定 |')
emit('|---|---|---|---|---|---|---|')
cur = now or st
for i, ax in enumerate(AXES):
    a = pre_vals[i] if pre_vals else None
    b = cur[i] if cur else None
    if a is None or b is None:
        emit('| %s | %s | ? | ? | | | 数据缺失 |' % (ax, FW[i]))
        continue
    d = b - a
    near_raw = abs(b - RAW[i]) < 1.5
    if near_raw and abs(d) > 5:
        verdict = '**丢定基 ✗**'
    elif abs(d) < 0.5:
        verdict = '未变 ✓'
    else:
        verdict = '变化 %+.2f°（需判断：下落 or 参考）' % d
    emit('| %s | %s | %+9.4f | %+9.4f | %+.3f | %s (本轴原始帧≈%+.2f) | %s |'
         % (ax, FW[i], a, b, d, '**是**' if near_raw else '否', RAW[i], verdict))
emit('')
with open(OUT, 'a', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
print('-> 追加写入 %s' % OUT)
