#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按维护工具证实的地址格式重试写 H0C.02（校零使能）= 1 到 J2。
   地址格式：6 位十六进制 <index:4><sub:2>，如 200C03 = 0x200C:03 = HC.02。"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
URL = 'http://%s:22000/settings/modifyServoParams' % HOST


def run(cmd, t=45):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


VARIANTS = [
    ('1 裸key 200C03 + body数组 + 字符串轴名', {'body': [{'key': '200C03', 'servoNum': 'J2', 'value': 1}]}),
    ('2 裸key 200c03 小写', {'body': [{'key': '200c03', 'servoNum': 'J2', 'value': 1}]}),
    ('3 addr前缀 + body数组（与读成功那次同形）', {'body': [{'key': 'addr200C03', 'servoNum': 'J2', 'value': 1}]}),
    ('4 裸key + 数组直接是 body', {'200C03': 1}),
]

mark = run("grep -ac 'writeSDO\\|sdo write' %s" % LOG).strip()
print('=== 写前日志里 writeSDO/sdo write 行数 = %s ===' % mark)

for name, body in VARIANTS:
    print('')
    print('--- 变体 %s ---' % name)
    print('    body = %s' % json.dumps(body, ensure_ascii=False))
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print('    -> HTTP %s（%.1fs） %s' % (r.status, time.time() - t0,
                                                  r.read()[:160].decode('utf-8', 'replace')))
    except urllib.error.HTTPError as e:
        print('    -> HTTP %s（%.1fs）' % (e.code, time.time() - t0))
    except Exception as e:  # noqa: BLE001
        print('    -> EXC %s（%.1fs）' % (type(e).__name__, time.time() - t0))
    time.sleep(2)
    out = run("grep -a 'writeSDO\\|sdo write\\|modifyServoParams\\|parseAndReqSet' %s | tail -5 | cut -c1-165" % LOG)
    print('    日志：%s' % (out.strip() if out.strip() else '(无)'))
    time.sleep(1)

print('')
print('=== 事后：writeSDO/sdo write 行数 ===')
print(run("grep -ac 'writeSDO\\|sdo write' %s" % LOG).strip())
