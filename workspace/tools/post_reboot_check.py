#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重启后只读检查：app 版本、六轴读数、固件版本字、标零相关日志。"""
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


def run(cmd, t=45):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def api(cmd):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(0.9)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', '')
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


print('=== 控制器 ===')
print(run('date; uptime; pidof codesyscontrol'))
print('app md5  : %s' % run('md5sum /dobot/userdata/codesys/allST/Application.app').split()[0])
print('')
print('=== 读数（未使能，先不动）===')
print('RobotMode : %s' % api('RobotMode()'))
print('GetErrorID: %s' % api('GetErrorID()')[:120])
print('GetAngle  : %s' % api('GetAngle()'))
print('')
print('=== 固件版本字 ===')
for axis, slave in [('J1', 3), ('J2', 4), ('J3', 5), ('J4', 6), ('J5', 7), ('J6', 8)]:
    v = sdo(axis, 'addr500007', 20480, slave)
    print('  %s (slave %d) = %s' % (axis, slave, '0x%04X' % v if v is not None else '?'))
print('')
print('=== 最近的标零/使能日志 ===')
print(run("grep -a 'calihome\\|HomeNumdone\\|robot enabled\\|robot disabled\\|AlarmSysSetBit' %s | tail -8 | cut -c1-150" % L))
