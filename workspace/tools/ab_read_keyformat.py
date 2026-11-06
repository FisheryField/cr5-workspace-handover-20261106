#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B：用不同 key 格式读同一批厂商参数，找出"能被驱动器回答"的那种。
   对照：已知能读通的 0x6064（addr606400）。"""
import json
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
URL = 'http://192.168.5.1:22000/settings/readServoParams'


def run(cmd, t=45):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


# (标签, key, 期望 index, 期望 sub)
TESTS = [
    ('控制组: 0x6064 裸key', '606400', 0x6064, 0),
    ('控制组: 0x6064 addr前缀', 'addr606400', 0x6064, 0),
    ('H01.17 裸key 200112', '200112', 0x2001, 0x12),
    ('H01.17 addr前缀', 'addr200112', 0x2001, 0x12),
    ('H0C.02 裸key 200C03', '200C03', 0x200C, 0x03),
    ('H0C.02 小写 200c03', '200c03', 0x200C, 0x03),
    ('H01.17 十进制式 200118', '200118', 0x2001, 0x18),
]

for label, key, exp_idx, exp_sub in TESTS:
    body = {'body': [{'key': key, 'servoNum': 'J2'}]}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    status = '?'
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            status = 'HTTP %s' % r.status
            r.read()
    except Exception as e:  # noqa: BLE001
        status = 'EXC %s' % type(e).__name__
    time.sleep(2.5)
    out = run("grep -a 'sdo read' %s | tail -4 | cut -c1-165" % LOG)
    got = []
    for line in out.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m:
            got.append((int(m.group(2)), int(m.group(3)), m.group(4), 'fail' in line))
    print('== %-26s key=%-12s %s' % (label, key, status))
    for idx, sub, val, isfail in got:
        mark = ''
        if idx == exp_idx and sub == exp_sub:
            mark = '   <<< 本次请求' + ('（有回值 ✓）' if isfail else '（仅回显 ✗）')
        print('     index=%-6d sub=%-3d value=%-8s %s%s' % (idx, sub, val, 'fail' if isfail else 'echo', mark))
    if not got:
        print('     (无 readSDO 行)')
    print('')
