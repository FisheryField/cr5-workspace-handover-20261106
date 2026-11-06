#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""试写 H0C.02（编码器校零使能，0x200C:03）= 1 到 J2，用正确 body 形状；
   记录 HTTP 状态 + 日志证据（modifyServoParams / writeSDO / servoParams.json）。"""
import json
import subprocess
import sys
import time
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
    ('A 带 body 数组 + 字符串轴名', {'body': [{'key': 'addr200c03', 'servoNum': 'J2', 'value': 1}]}),
    ('B 带 body 数组 + 数字轴号', {'body': [{'key': 'addr200c03', 'servoNum': 4, 'value': 1}]}),
    ('C 单对象无 body 包裹', {'key': 'addr200c03', 'servoNum': 'J2', 'value': 1}),
]

print('=== 写之前：日志标记位置 ===')
before = run("grep -ac 'modifyServoParams\\|writeSDO' %s" % LOG).strip()
print('  匹配行数(之前) = %s' % before)

for name, body in VARIANTS:
    print('')
    print('--- 变体 %s ---' % name)
    print('    body = %s' % json.dumps(body, ensure_ascii=False))
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print('    -> HTTP %s  %s' % (r.status, r.read()[:200].decode('utf-8', 'replace')))
    except urllib.error.HTTPError as e:  # noqa: PERF203
        print('    -> HTTP %s  %s' % (e.code, e.read()[:200].decode('utf-8', 'replace')))
    except Exception as e:  # noqa: BLE001
        print('    -> EXC %s: %s' % (type(e).__name__, e))
    time.sleep(2)
    out = run("grep -a 'modifyServoParams\\|writeSDO\\|parseAndReqSet\\|ServoParamsWrite\\|sdo write' %s | tail -6 | cut -c1-170" % LOG)
    print('    日志：')
    print(out.strip() if out.strip() else '    (无相关日志行)')
    if 'HTTP 200' in str(locals().get('_last', '')) or True:
        pass
    time.sleep(1)

print('')
print('=== servoParams.json（写路由会落盘留痕）===')
print(run("ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null; "
          "grep -a '200c03\\|200C03' /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null | head -5"))
