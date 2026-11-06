#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把控制模式设回 TCP（controlMode=1），并确认 API 恢复。
   只调 /settings/controlMode，不动运动、不改文件。"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = [r'C:\Program Files\PyManager\python.exe', r'D:\mydata\workspace\tools\rssh.py']
D = '/dobot/userdata/CR5_sys_files/project/logs/all'
URL = 'http://%s:22000/settings/controlMode' % HOST


def rq(cmd, t=60):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def post(payload, label):
    try:
        req = urllib.request.Request(URL, data=payload,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            st, body = r.status, r.read().decode('utf-8', 'replace')[:120]
    except urllib.error.HTTPError as e:
        st, body = e.code, 'HTTPError'
    except Exception as e:  # noqa: BLE001
        st, body = -1, '%s' % type(e).__name__
    time.sleep(1.2)
    lg = rq("grep -a 'settControlMode\\|controlMode' %s/log 2>/dev/null | tail -3 | cut -c1-180" % D)
    print('  %-26s HTTP %-5s %-14s' % (label, st, body))
    if lg.strip():
        print('     ' + lg.strip().replace('\n', '\n     ')[:520])
    return st


print('=== 0) 当前控制模式（从日志）===')
print(rq("grep -a 'controlMode=' %s/log 2>/dev/null | tail -3 | cut -c1-190" % D).strip())
print('')

print('=== 1) 试各种 payload 形状把模式设成 TCP(1) ===')
for payload, label in [
    (b'{"value":1}', 'A value=1'),
    (b'{"controlMode":1}', 'B controlMode=1'),
    (b'{"body":{"controlMode":1}}', 'C body.controlMode=1'),
    (b'{"body":[{"controlMode":1}]}', 'D body[].controlMode=1'),
    (b'1', 'E 裸数字 1'),
    (b'{"enable":1}', 'F enable=1'),
]:
    st = post(payload, label)
    if st == 200:
        print('     ⇒ HTTP 200，继续下一步验证')
        break

print('')
print('=== 2) 验证：日志里的最新 controlMode + API 是否恢复 ===')
print(rq("grep -a 'controlMode=' %s/log 2>/dev/null | tail -4 | cut -c1-190" % D).strip())
print('')
try:
    s = __import__('socket').create_connection((HOST, 30003), timeout=8)
    s.settimeout(8)
    s.sendall(b'RobotMode()\n')
    time.sleep(1.2)
    print('  30003 RobotMode :', s.recv(4096).decode('utf-8', 'replace').strip()[:120])
    s.close()
except Exception as e:  # noqa: BLE001
    print('  30003 仍不可用:', type(e).__name__, e)
