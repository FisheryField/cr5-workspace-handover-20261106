#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""① 试 HTTP 清报警（/interface/resetCollision 等）② 回退原版主控（为标零准备）。"""
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


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def post(path, payload=b'{}', label=''):
    try:
        req = urllib.request.Request('http://%s:22000%s' % (HOST, path), data=payload,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            st, body = r.status, r.read().decode('utf-8', 'replace')[:110]
    except urllib.error.HTTPError as e:
        st, body = e.code, 'HTTPError'
    except Exception as e:  # noqa: BLE001
        st, body = -1, '%s' % type(e).__name__
    print('  %-38s HTTP %-5s %s' % (label or path, st, body))
    time.sleep(1.0)
    return st


print('=== 1) 试各种"清报警"路由 ===')
for path, payload, label in [
    ('/interface/resetCollision', b'{}', 'resetCollision'),
    ('/interface/clearError', b'{}', 'clearError'),
    ('/settings/clearError', b'{}', 'settings/clearError'),
    ('/interface/clearAlarm', b'{}', 'clearAlarm'),
    ('/settings/clearAlarms', b'{}', 'settings/clearAlarms'),
    ('/interface/resetError', b'{}', 'resetError'),
]:
    post(path, payload, label)

print('')
print('  --- 清报警日志（看有没有真的进去）---')
print(rq("grep -a 'clearError\\|ClearError\\|clearAlarm' %s/log 2>/dev/null | tail -4 | cut -c1-180" % D).strip())

print('')
print('=== 2) 驱动器故障码现状 ===')
print(rq("grep -a 'logServoError' %s/log 2>/dev/null | tail -4 | cut -c1-140" % D).strip())

print('')
print('=== 3) 回退原版主控（标零前置条件）===')
print(rq("sh /dobot/userdata/zero_cycle.sh to-stock", t=120).strip())

print('')
print('=== 4) J2 限位与当前读数（确认 ±280 仍在）===')
print(rq("md5sum /dobot/userdata/CR5_sys_files/project/properties/structure.json").strip())
print(rq("grep -a 'PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -1 | cut -c1-205" % D).strip())
print('  （structure 期望 md5 = 60bc143a3233d0833206d0fbbb7d6c8b）')
