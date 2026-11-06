#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 modifyServoParams 的可疑 payload 变体，逐个试探（全部写当前值 0，无害）。
   每次记录：HTTP 状态 + 日志里是否出现 sdo write。"""
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = [r'C:\Program Files\PyManager\python.exe', r'D:\mydata\workspace\tools\rssh.py']
D = '/dobot/userdata/CR5_sys_files/project/logs/all'
URL = 'http://%s:22000/settings/modifyServoParams' % HOST


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def post(data, ctype='application/json', method='POST'):
    try:
        req = urllib.request.Request(URL, data=data,
                                     headers={'Content-Type': ctype}, method=method)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:130]
    except urllib.error.HTTPError as e:
        return e.code, 'HTTPError'
    except Exception as e:  # noqa: BLE001
        return -1, '%s: %s' % (type(e).__name__, str(e)[:80])


VARIANTS = [
    ('A 模板原样(J6)', b'{"body":[{"key":"addr200C01","servoNum":"J6","value":0}]}',
     'application/json', 'POST'),
    ('B 裸数组', b'[{"key":"addr200C01","servoNum":"J2","value":0}]', 'application/json', 'POST'),
    ('C body=对象', b'{"body":{"key":"addr200C01","servoNum":"J2","value":0}}', 'application/json', 'POST'),
    ('D value=字符串', b'{"body":[{"key":"addr200C01","servoNum":"J2","value":"0"}]}',
     'application/json', 'POST'),
    ('E 加 type 字段', b'{"body":[{"key":"addr200C01","servoNum":"J2","value":0,"type":0}]}',
     'application/json', 'POST'),
    ('F form-urlencoded', b'key=addr200C01&servoNum=J2&value=0',
     'application/x-www-form-urlencoded', 'POST'),
    ('G JSON+query 参数', b'{"body":[{"key":"addr200C01","servoNum":"J2","value":0}]}',
     'application/json', 'POST?key=addr200C01&servoNum=J2&value=0'),
    ('H 顶层就是对象', b'{"key":"addr200C01","servoNum":"J2","value":0}', 'application/json', 'POST'),
]

for label, data, ctype, tail in VARIANTS:
    url = URL + (tail[4:] if tail.startswith('POST?') else '')
    try:
        req = urllib.request.Request(url, data=data, headers={'Content-Type': ctype}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            st, body = r.status, r.read().decode('utf-8', 'replace')[:130]
    except urllib.error.HTTPError as e:
        st, body = e.code, 'HTTPError'
    except Exception as e:  # noqa: BLE001
        st, body = -1, '%s' % type(e).__name__
    time.sleep(1.2)
    lg = rq("grep -a 'sdo write\\|modifyServoParams\\|value is\\|out of range\\|invalid' %s/log 2>/dev/null | tail -3 | cut -c1-165" % D)
    has_w = 'sdo write' in lg
    print('%-20s HTTP %-5s %-12s  日志有sdo write=%s' % (label, st, body.replace('\n', ' ')[:40], has_w))
    if has_w:
        print('     ', lg.strip().replace('\n', '\n      ')[:600])
        break
