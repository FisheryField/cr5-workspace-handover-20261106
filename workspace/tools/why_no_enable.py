#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查为什么上不了使能：模式/报警/急停/驱动器故障码(0x603F)/日志拒绝原因。"""
import json
import re
import socket
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'


def run(cmd, t=60):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def api(cmd, wait=0.9):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


def sdo(axis, key, idx, slave):
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                 data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception:  # noqa: BLE001
        return None
    time.sleep(0.8)
    txt = run("grep -a 'sdo read' %s | tail -3" % L)
    best = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == idx:
            v = int(float(m.group(4)))
            if 'fail' in line:
                return v
            best = v
    return best


print('=== API ===')
print('RobotMode  : %s' % api('RobotMode()'))
print('GetErrorID : %s' % api('GetErrorID()'))
print('GetAngle   : %s' % api('GetAngle()'))
print('')
print('=== 急停状态与报警位 ===')
print(run("grep -a 'emergencyStopStatus' %s | tail -2 | cut -c1-130" % L))
print(run("grep -a 'AlarmSysSetBit\\|AlarmSysClearBit' %s | tail -6 | cut -c1-130" % L))
print('')
print('=== 使能被拒 / 驱动器错误 ===')
print(run("grep -a \"can't enable\\|exist an error\\|enable robot\\|robot enabled\\|logServoError\" %s | tail -8 | cut -c1-170" % L))
print('')
print('=== 逐轴驱动器故障码 0x603F ===')
for axis, slave in [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]:
    v = sdo(axis, 'addr603f00', 0x603F, slave)
    print('  %s (slave %d) 0x603F = %s' % (axis, slave, v if v is not None else '?'))
print('')
print('=== 状态字 0x6041 / 控制字 0x6040 ===')
for axis, slave in [('J3', 5)]:
    for key, idx, name in [('addr604100', 0x6041, '0x6041 状态字'), ('addr604000', 0x6040, '0x6040 控制字')]:
        v = sdo(axis, key, idx, slave)
        print('  %s %s = %s' % (axis, name, ('0x%04X' % v) if v is not None else '?'))
print('')
print('=== 日志尾部 ===')
print(run("tail -8 %s | cut -c1-170" % L))
