#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把当前姿态标为零：enable -> POST /calibrate/home -> 观察 HomeNumdone/servo calihome done -> 读姿态 -> disable。"""
import json
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'


def run(cmd, t=45):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def post(path, body='{}'):
    req = urllib.request.Request('http://%s:22000%s' % (HOST, path), data=body.encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:120]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:120]


def angles():
    try:
        import socket
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall(b'GetAngle()\n')
        time.sleep(0.8)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        m = re.search(r'\{([-0-9.,\s]+)\}', d)
        if m:
            return [float(x) for x in m.group(1).split(',')]
    except Exception:  # noqa: BLE001
        pass
    return None


marker = int(run('wc -l < %s' % L).split()[0])
print('=== 标零前 ===')
print('  log 行号 = %d' % marker)
print('  姿态     = %s' % angles())
print('  报警/模式 = %s' % run("grep -a 'AlarmSysSetBit\\|emergencyStopStatus' %s | tail -3 | cut -c1-120" % L).replace('\n', ' | '))

print('')
print('=== 使能 ===')
print('  POST /settings/controlMode {"controlMode":"enable"} -> %s' % (post('/settings/controlMode', '{"controlMode":"enable"}'),))
time.sleep(3)
print('  姿态 = %s' % angles())
print('  模式 = %s' % run('curl -s --max-time 5 -d "{}" http://127.0.0.1:29999 2>/dev/null | head -1'))

print('')
print('=== 标零 ===')
print('  POST /calibrate/home -> %s' % (post('/calibrate/home'),))
done = False
last = ''
for i in range(16):
    time.sleep(1.5)
    last = run("tail -n +%d %s | grep -a 'HomeNumdone\\|calihome\\|robot enabled\\|robot disabled\\|AlarmSysSetBit'" % (marker + 1, L))
    if 'servo calihome done' in last:
        done = True
        break
print('  --- 新日志行 ---')
for line in last.splitlines()[-14:]:
    print('   ' + line.strip()[:160])

print('')
print('=== 标零后 ===')
print('  姿态 = %s' % angles())
print('  homeEncoder.json 里的 innerEncoder:')
print(run("grep -A 8 'innerEncoder' /dobot/userdata/project/settings/function/homeEncoder.json | head -10"))
print('')
print('=== 下使能 ===')
print('  POST /settings/controlMode {"controlMode":"disable"} -> %s' % (post('/settings/controlMode', '{"controlMode":"disable"}'),))
time.sleep(2)
print('  姿态 = %s' % angles())
print('')
print('VERDICT: %s' % ('标零完成 ✓' if done else '未确认（看上面日志）'))
