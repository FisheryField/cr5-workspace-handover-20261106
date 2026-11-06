#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDO 写通道探针（安全版）：
   1) 先用设备自带模板的确切形状，写 H0C.00(addr200C01) = 0（其当前值，无变化）
   2) 再写 H0C.02(addr200C03) = 0（其当前值，无变化）
   3) 每步都读回校验、并抓日志里的 sdo write 行
   不改变任何参数值。"""
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


def logtail(n=4):
    return rq("grep -a 'sdo write\\|sdo read\\|modifyServoParams\\|ServoParams' %s/log 2>/dev/null | tail -%d | cut -c1-175" % (D, n)).strip()


def sdo_read(idx, sub, axis='J2', slave=4):
    key = 'addr%04X%02X' % (idx, sub)
    body = {'body': [{'key': key, 'servoNum': axis}]}
    try:
        req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        return None, 'HTTPERR %s' % type(e).__name__
    time.sleep(0.9)
    txt = rq("grep -a 'sdo read' %s/log 2>/dev/null | tail -4" % D)
    val = None
    for line in txt.splitlines():
        m = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
        if m and int(m.group(1)) == slave and int(m.group(2)) == idx and int(m.group(3)) == sub:
            val = int(float(m.group(4)))
    if val is not None and val >= (1 << 31):
        val -= (1 << 32)
    return val, None


def sdo_write_raw(payload_bytes, label):
    """用给定的原始 JSON 字节 POST。返回 (status, body)。"""
    print('  POST /settings/modifyServoParams   payload = %s' % payload_bytes.decode('utf-8', 'replace'))
    try:
        req = urllib.request.Request('http://%s:22000/settings/modifyServoParams' % HOST,
                                     data=payload_bytes,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:160]
    except urllib.error.HTTPError as e:  # noqa: PERF203
        return e.code, (e.read().decode('utf-8', 'replace')[:160] if e.fp else '')
    except Exception as e:  # noqa: BLE001
        return -1, '%s: %s' % (type(e).__name__, e)


print('=== 0) 基线读取 ===')
for idx, sub, name in ((0x200C, 1, 'H0C.00 故障复位'), (0x200C, 3, 'H0C.02 校零使能'), (0x607C, 0, '0x607C 原点偏移')):
    v, err = sdo_read(idx, sub)
    print('  %-22s = %s %s' % (name, v, err or ''))

print('')
print('=== 1) 写 H0C.00 = 0（当前值，无变化）===')
st, body = sdo_write_raw(b'{"body":[{"key":"addr200C01","servoNum":"J2","value":0}]}', 'H0C.00=0')
print('  HTTP %s  %s' % (st, body))
time.sleep(1.5)
print('  日志尾部:')
print('   ', logtail(5).replace('\n', '\n    ')[:700])

print('')
print('=== 2) 写 H0C.02 = 0（当前值，无变化）===')
st, body = sdo_write_raw(b'{"body":[{"key":"addr200C03","servoNum":"J2","value":0}]}', 'H0C.02=0')
print('  HTTP %s  %s' % (st, body))
time.sleep(1.5)
print('  日志尾部:')
print('   ', logtail(5).replace('\n', '\n    ')[:700])

print('')
print('=== 3) 读回校验（应仍为 0）===')
for idx, sub, name in ((0x200C, 1, 'H0C.00'), (0x200C, 3, 'H0C.02'), (0x607C, 0, '0x607C')):
    v, err = sdo_read(idx, sub)
    print('  %-12s = %s %s' % (name, v, err or ''))

print('')
print('=== 4) 结论 ===')
print('  若 HTTP 200 且日志出现 sdo write 行 ⇒ 写通道已通 ✓（且参数值未变 ✓）')
print('  若 HTTP 400/挂起 ⇒ 该形状仍不对，需换 key 前缀或字段名')
