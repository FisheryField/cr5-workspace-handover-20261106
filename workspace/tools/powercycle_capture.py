#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下电/上电数据采集（全程只读）。

每轮采集：
  1) API  : RobotMode() / GetAngle() / GetErrorID()
  2) SDO  : 六轴 0x6064（POST :22000/settings/readServoParams，值在日志 readSDO 行）
  3) 日志 : 最新 PoseTrace 的 J2（nextPos / (PDO) / gActualPosition）
控制器掉线时记 DOWN，恢复后记 RECOVERED 并继续。
输出：workspace/powercycle_capture.log
"""
import datetime
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'powercycle_capture.log')
SCALE = 360.0 / (20000 * 101)
AXES = [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]
DURATION_MIN = 45


def log(msg):
    line = '%s | %s' % (datetime.datetime.now().strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    with open(OUT, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def api(cmds):
    try:
        s = socket.create_connection((HOST, 30003), timeout=6)
        s.settimeout(5)
        res = []
        for c in cmds:
            s.sendall((c + '\n').encode())
            time.sleep(0.35)
            try:
                res.append(s.recv(8192).decode('utf-8', 'replace').strip())
            except socket.timeout:
                res.append('<no reply>')
        s.close()
        return res
    except Exception:  # noqa: BLE001
        return None


def sdo(axis, slave, key='addr606400'):
    url = 'http://%s:22000/settings/readServoParams' % HOST
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception:  # noqa: BLE001
        return None
    time.sleep(0.4)
    try:
        out = subprocess.run([RSH, "grep -a 'readSDO' %s | tail -2" % LOG],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:  # noqa: BLE001
        return None
    for line in reversed(out.splitlines()):
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == 24676:
            v = float(m.group(4))
            return '%d(%.4f°)' % (int(v), v * SCALE)
    return None


def pose_trace_j2():
    try:
        out = subprocess.run([RSH, "grep -a 'PoseTrace' %s | tail -3" % LOG],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:  # noqa: BLE001
        return ''
    vals = []
    for line in out.splitlines():
        if ':  ' in line:
            parts = line.split(':  ')[-1].split(',')
            if len(parts) >= 6:
                vals.append(parts[1].strip())
    return '/'.join(vals)


def main():
    log('=== 采集开始（只读，%d 分钟）===' % DURATION_MIN)
    t0 = time.time()
    down = False
    while time.time() - t0 < DURATION_MIN * 60:
        a = api(['RobotMode()', 'GetAngle()', 'GetErrorID()'])
        if a is None:
            if not down:
                log('DOWN  —— 控制器不可达（可能正在下电）')
                down = True
            time.sleep(4)
            continue
        if down:
            log('RECOVERED —— 控制器已回来')
            down = False
        mode = a[0].split('{')[1].split('}')[0] if '{' in a[0] else '?'
        ang = a[1].split('{')[1].split('}')[0] if '{' in a[1] else '?'
        err = a[2].replace('\n', '').replace('\t', '')
        err = err.split('{', 1)[1].split('}', 1)[0] if '{' in err else err
        sdos = []
        for axis, slave in AXES:
            v = sdo(axis, slave)
            sdos.append('%s=%s' % (axis, v if v else '?'))
        log('mode=%s | angle=%s | err=%s' % (mode, ang, err[:60]))
        log('  6064: %s | PoseTrace_J2(nextPos/PDO/actual)=%s' % (' '.join(sdos), pose_trace_j2()))
        time.sleep(6)
    log('=== 采集结束 ===')


if __name__ == '__main__':
    sys.exit(main())
