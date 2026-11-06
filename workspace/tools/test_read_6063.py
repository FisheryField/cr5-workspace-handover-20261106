#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：测试厂商 HTTP SDO 通道能否读 0x6063 / 0x6062 / 0x6064（T4 的单次判定实验）。"""
import json
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
URL = 'http://192.168.5.1:22000/settings/readServoParams'
TESTS = [('J2', '0x6064 位置实际值', 'addr606400', 0x6064),
         ('J2', '0x6063 位置实际值(内部单位)', 'addr606300', 0x6063),
         ('J2', '0x6062 位置给定值', 'addr606200', 0x6062),
         ('J3', '0x6063 位置实际值(内部单位)', 'addr606300', 0x6063),
         ('J3', '0x6064 位置实际值', 'addr606400', 0x6064)]


def run(cmd, t=45):
    return subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                          stdin=subprocess.DEVNULL).stdout


for axis, name, key, index in TESTS:
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    status = '?'
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            status = 'HTTP %s %s' % (r.status, r.read()[:60].decode('utf-8', 'replace'))
    except Exception as e:  # noqa: BLE001
        status = 'EXC %s' % e
    print('== %s / %s (key=%s) -> %s' % (axis, name, key, status))
    time.sleep(1.2)
    out = run("grep -a 'sdo read' %s | tail -3 | cut -c1-150" % LOG)
    for line in out.strip().splitlines():
        print('    ' + line.strip())
    print('')
