#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用单轴 FoE 刷写：python tools/flash_slave_fw.py <slaveId> <文件名>
判据：/mToolServer/mToolServer.log 出现 foe write result is success.g_TempFoeWriteErrCode=0"""
import json
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
URL = 'http://192.168.5.1:22002/update/CR/singleFwAndXml'
LOG = '/mToolServer/mToolServer.log'

slave = int(sys.argv[1])
fname = sys.argv[2]
body = {"cabType": "big", "cabVersion": "V1", "operationType": "start",
        "slaveId": slave, "updateFile": fname, "updateFile2": "", "updateType": "firmware"}
print('POST %s' % URL)
print(json.dumps(body, ensure_ascii=False))
req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                             headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print('-> HTTP %s %s' % (r.status, r.read()[:120].decode('utf-8', 'replace')))
except Exception as e:  # noqa: BLE001
    print('-> EXC %s: %s' % (type(e).__name__, e))

ok = False
for i in range(12):
    time.sleep(5)
    out = subprocess.run([RSH, 'tail -12 %s' % LOG], capture_output=True, text=True,
                         timeout=60, stdin=subprocess.DEVNULL).stdout
    for line in out.splitlines():
        if 'foe write result' in line or 'start FoE write' in line or 'state to boot' in line:
            print('   %s' % line.strip()[:160])
    if 'foe write result' in out:
        ok = 'ErrCode=0' in out
        print('\n>>> 判据: %s' % ('成功 (ErrCode=0) ✓✓' if ok else '失败 ✗'))
        break
print('tail:\n%s' % out.strip()[-600:])
