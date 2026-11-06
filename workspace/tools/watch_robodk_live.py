#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时监视：日志里的 RoboDK 指令 + 30003 实时姿态（默认 120 秒）。
   用法: python tools/watch_robodk_live.py [秒数]
"""
import json
import re
import socket
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 120


def run(cmd, t=30):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def angle():
    try:
        s = socket.create_connection((HOST, 30003), timeout=4)
        s.settimeout(4)
        s.sendall(b'GetAngle()\n')
        time.sleep(0.35)
        d = s.recv(4096).decode('utf-8', 'replace')
        s.close()
        m = re.search(r'\{([-0-9.,\s]+)\}', d)
        if m:
            return [float(x) for x in m.group(1).split(',')]
    except Exception:  # noqa: BLE001
        pass
    return None


line0 = int(run('wc -l < %s' % L).split()[0])
print('baseline log line = %d  (监视 %d 秒)' % (line0, DUR))
prev = angle()
print('t=0  pose = %s' % (['%+.4f' % v for v in prev] if prev else None))

newlines = 0
t0 = time.time()
while time.time() - t0 < DUR:
    time.sleep(2)
    out = run('tail -n +%d %s' % (line0 + 1, L))
    if out.strip():
        for line in out.strip().splitlines():
            if re.search(r'recv =|queuedCmdIndex|AlarmSysSetBit|logServoError|robot enabled|robot disabled|PreDeal|finsh', line):
                print('[log %5.1fs] %s' % (time.time() - t0, line.strip()[:165]))
        line0 += len(out.strip().splitlines())
        newlines += 1
    cur = angle()
    if cur and prev and any(abs(a - b) > 0.02 for a, b in zip(cur, prev)):
        print('[pose %5.1fs] %s   <== 姿态在变！' % (time.time() - t0, ['%+.4f' % v for v in cur]))
    prev = cur or prev

print('')
print('结束。姿态 = %s' % (['%+.4f' % v for v in prev] if prev else None))
