#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：逐轴读 0x6062 / 0x6063 / 0x6064 + 版本字，并按"固件分组"比较关系。
   T4 判据：若两版的 0x6063 关系不同 ⇒ 差异在编码器 preset 层；若只有 0x6064 不同 ⇒ 差异在 fp()。"""
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
# 当前已知固件状态（2026-09-26）：J6 已刷原厂 D8，J2 为 3.1.5.0+T5 补丁，其余 3.1.5.0
FW = {'J1': '3.1.5.0', 'J2': '3.1.5.0+T5', 'J3': '3.1.5.0',
      'J4': '3.1.5.0', 'J5': '3.1.5.0', 'J6': 'D8'}
OBJS = [('0x6062', 'addr606200', 24674), ('0x6063', 'addr606300', 24675),
        ('0x6064', 'addr606400', 24676), ('ver', 'addr500007', 20480)]


def run(cmd, t=45):
    return subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                          stdin=subprocess.DEVNULL).stdout


def read(axis, key, index, slave):
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
    txt = run("grep -a 'sdo read' %s | tail -3" % LOG)
    best = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == index:
            v = int(float(m.group(4)))
            if 'fail' in line:
                return v
            best = v
    return best


lines = []
now = time.strftime('%Y-%m-%d %H:%M:%S')
lines.append('## 0x6062/0x6063/0x6064 + 版本字（D8 vs 3.1.5.0 判据）  %s' % now)
lines.append('')
hdr = '| 轴 | slave | 固件 | 0x6062 | 0x6063 | 0x6064 | 版本字 | 关系 |'
lines.append(hdr)
lines.append('|---|' + '---|' * 7)
print('## %s' % now)
print(hdr)
for axis, slave in AXES:
    vals = [read(axis, k, i, slave) for _, k, i in OBJS]
    v62, v63, v64, ver = vals
    ver_s = '0x%04X' % ver if ver is not None else '?'
    got = [v for v in (v62, v63, v64) if v is not None]
    if len(got) < 3:
        rel = '读取不全'
    elif len(set(got)) == 1:
        rel = '三者相同'
    elif v63 == v64 and v62 != v63:
        rel = '6062 不同、6063=6064'
    elif v62 == v63 and v64 != v62:
        rel = '6062=6063、6064 不同'
    else:
        rel = '三者各不同'
    line = '| %s | %d | %s | %s | %s | %s | %s | %s |' % (
        axis, slave, FW[axis],
        *['?' if v is None else str(v) for v in (v62, v63, v64)], ver_s, rel)
    print(line)
    lines.append(line)
lines.append('')
with open(OUT, 'a', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('\n-> 追加写入 %s' % OUT)
