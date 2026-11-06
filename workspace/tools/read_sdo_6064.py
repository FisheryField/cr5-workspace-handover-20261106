# -*- coding: utf-8 -*-
"""只读：请求读 J2（及六轴）的 0x6064，然后从日志取 readSDO 行的 value。
   H01.17 编码器位置角 = 0x2001:18 -> addr200118（厂商参数视图的编码器值）。"""
import json
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
URL = 'http://192.168.5.1:22000/settings/readServoParams'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
SCALE = 360.0 / (20000 * 101)

REQS = [('J2', 'addr606400'), ('J2', 'addr200118'),
        ('J1', 'addr606400'), ('J3', 'addr606400'), ('J4', 'addr606400'),
        ('J5', 'addr606400'), ('J6', 'addr606400')]

for axis, key in REQS:
    body = {'body': [{'key': key, 'servoNum': axis}]}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        print('%-3s %-12s request EXC %s' % (axis, key, e))
    time.sleep(1.5)
    # 取日志里最新的 readSDO 行
    try:
        out = subprocess.run([RSH, "grep -a 'readSDO' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -3"],
                             capture_output=True, text=True, timeout=40).stdout
    except Exception as e:  # noqa: BLE001
        out = 'grep EXC %s' % e
    lines = [l for l in out.splitlines() if l.strip()]
    print('== %-3s %-12s ==' % (axis, key))
    for l in lines[-2:]:
        print('   ', l.strip()[:200])
        try:
            if 'value=' in l:
                v = float(l.split('value=')[1].split()[0].strip(';,'))
                print('      -> %g counts = %.5f deg' % (v, -v * SCALE))
        except Exception:  # noqa: BLE001
            pass
