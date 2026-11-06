#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向控制器 mToolServer 发单轴 FoE 刷写请求（J2 = slave 4），然后读日志判定结果。"""
import json
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
URL = 'http://192.168.5.1:22002/update/CR/singleFwAndXml'
LOG = '/mToolServer/mToolServer.log'

body = {
    "cabType": "big",
    "cabVersion": "V1",
    "operationType": "start",
    "slaveId": 4,
    "updateFile": "CR5_Servo_ST_FOE_V3.2.D.8.bin",
    "updateFile2": "",
    "updateType": "firmware",
}
print('POST %s' % URL)
print(json.dumps(body, ensure_ascii=False))
req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                             headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print('-> HTTP %s  %s' % (r.status, r.read()[:200].decode('utf-8', 'replace')))
except Exception as e:  # noqa: BLE001
    print('-> EXC %s: %s' % (type(e).__name__, e))

for i in range(9):
    time.sleep(5)
    out = subprocess.run([RSH, "tail -14 %s" % LOG], capture_output=True, text=True,
                         timeout=60).stdout
    sys.stdout.write('\n---- t+%ds 日志 ----\n%s\n' % ((i + 1) * 5, out.strip()))
    if 'foe write result' in out or ('ErrCode' in out and 'success' in out):
        break
