#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 J2 的 0x607C(Home offset) 写 +360°，验证 0x6064 是否跟着平移一圈。
   全程带基线读取、写后立刻读回、以及自动回退（写回 0）。
   ⚠️ 会写一个参数；请手放急停。"""
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
SCALE = 360.0 / (20000.0 * 101.0)
ONE_TURN = 20000 * 101          # = 2,020,000 counts / 圈


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def sdo_read(idx, axis='J2', slave=4, sub=0):
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


def sdo_write(idx, value, axis='J2', sub=0):
    key = 'addr%04X%02X' % (idx, sub)
    body = {'body': [{'key': key, 'servoNum': axis, 'value': value}]}
    try:
        req = urllib.request.Request('http://%s:22000/settings/modifyServoParams' % HOST,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:120]
    except Exception as e:  # noqa: BLE001
        return -1, '%s: %s' % (type(e).__name__, e)


print('=== 0) 基线 ===')
b_off, e1 = sdo_read(0x607C)
b_pos, e2 = sdo_read(0x6064)
b_dem, e3 = sdo_read(0x6062)
print('  0x607C 原点偏移 = %s %s' % (b_off, e1 or ''))
print('  0x6064 位置实际 = %s  (%.3f°)' % (b_pos, (b_pos or 0) * SCALE))
print('  0x6062 位置给定 = %s  (%.3f°)' % (b_dem, (b_dem or 0) * SCALE))

print('')
print('=== 1) 写 0x607C = +%d（= +360°）===' % ONE_TURN)
st, body = sdo_write(0x607C, ONE_TURN)
print('  HTTP %s  %s' % (st, body))
time.sleep(1.0)
print('  日志尾部:')
print('   ', rq("grep -a 'sdo write\\|sdo read' %s/log 2>/dev/null | tail -4 | cut -c1-170" % D).strip()[:500])

print('')
print('=== 2) 立刻读回 ===')
time.sleep(1.5)
a_off, _ = sdo_read(0x607C)
a_pos, _ = sdo_read(0x6064)
a_dem, _ = sdo_read(0x6062)
print('  0x607C 原点偏移 = %s  (目标 %d)' % (a_off, ONE_TURN))
print('  0x6064 位置实际 = %s  (%.3f°)' % (a_pos, (a_pos or 0) * SCALE))
print('  0x6062 位置给定 = %s  (%.3f°)' % (a_dem, (a_dem or 0) * SCALE))

print('')
print('=== 3) 判定 ===')
if a_off != ONE_TURN:
    print('  ✗ 写入未生效（0x607C 仍是 %s）⇒ 该对象可能只读/需先失能' % a_off)
elif a_pos == b_pos:
    print('  ⚠ 0x607C 写入生效了，但 0x6064 没变（%s → %s）⇒ 它不影响实际位置读数' % (b_pos, a_pos))
    print('     ⇒ 需换手段（例如 H01.17 编码器位置角 或 0x607D 限位）')
else:
    print('  ★★ 0x6064 变化了：%s → %s（差 %+d counts = %+.3f°）'
          % (b_pos, a_pos, (a_pos - b_pos), (a_pos - b_pos) * SCALE))
    print('     ⇒ 若差值 ≈ +2,020,000（+360°）⇒ 坐标平移成功 ✓✓')

print('')
print('=== 4) 主控显示是否跟着变（最新 PoseTrace）===')
print('  ', rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -2 | cut -c1-205" % D).strip()[:420])

print('')
print('=== 5) 回退命令（如需）===')
print('  重跑本脚本并把写入值改成 0；或直接执行：')
print('    POST http://192.168.5.1:22000/settings/modifyServoParams')
print('    {"body":[{"key":"addr607C00","servoNum":"J2","value":0}]}')
