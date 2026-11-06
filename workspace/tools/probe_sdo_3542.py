#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读探测：3.5.4.2 上厂商伺服参数（SDO）通道是否可用。
   只读！不发运动、不写任何参数。"""
import json
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = [r'C:\Program Files\PyManager\python.exe', r'D:\mydata\workspace\tools\rssh.py']
D = '/dobot/userdata/CR5_sys_files/project/logs/all'


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def post(path, body, timeout=15):
    try:
        req = urllib.request.Request('http://%s:22000%s' % (HOST, path),
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'},
                                     method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:200]
    except Exception as e:  # noqa: BLE001
        return -1, '%s: %s' % (type(e).__name__, e)


print('=== A) 探 /settings/readServoParams（0x6064 位置实际，标准 CiA402，必答）===')
st, body = post('/settings/readServoParams', {'body': [{'key': 'addr606400', 'servoNum': 'J2'}]})
print('  HTTP %s  %s' % (st, body))
time.sleep(1.2)
print('  日志里的 sdo read 行:')
print('   ', rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -3 | cut -c1-190" % D).strip()[:420])

print('')
print('=== B) 探厂商参数 H01.17（0x2001:18 = addr200112，编码器位置角）===')
st, body = post('/settings/readServoParams', {'body': [{'key': 'addr200112', 'servoNum': 'J2'}]})
print('  HTTP %s  %s' % (st, body))
time.sleep(1.2)
print('  日志里的 sdo read 行:')
print('   ', rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -3 | cut -c1-190" % D).strip()[:420])

print('')
print('=== C) 探 H0C.02（0x200C:03 = addr200C03，编码器校零使能）===')
st, body = post('/settings/readServoParams', {'body': [{'key': 'addr200C03', 'servoNum': 'J2'}]})
print('  HTTP %s  %s' % (st, body))
time.sleep(1.2)
print('  日志里的 sdo read 行:')
print('   ', rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -3 | cut -c1-190" % D).strip()[:420])

print('')
print('=== D) 顺便看 0x603F 故障码（J2）===')
st, body = post('/settings/readServoParams', {'body': [{'key': 'addr603F00', 'servoNum': 'J2'}]})
print('  HTTP %s  %s' % (st, body))
time.sleep(1.2)
print('   ', rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -3 | cut -c1-190" % D).strip()[:420])
