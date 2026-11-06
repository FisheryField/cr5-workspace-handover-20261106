#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RoboDK 运动全程监控（只读）。
   线程A: 30004 实时流（robotMode / qActual / qdActual）
   线程B: API 轮询（GetAngle/RobotMode/GetErrorID，定期 GetPose）
   线程C: HTTP SDO 0x6062/0x6063/0x6064（若通道可用）
   全部带本地时间戳写入 monitor_<date>.log
"""
import json
import os
import re
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 600
OUT = os.path.join(r'D:\mydata\workspace',
                   'monitor_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
lock = threading.Lock()
stop = threading.Event()
fh = open(OUT, 'w', encoding='utf-8')
NAMES = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']


def w(tag, msg):
    with lock:
        fh.write('%s [%s] %s\n' % (time.strftime('%H:%M:%S'), tag, msg))
        fh.flush()
        print('%s [%s] %s' % (time.strftime('%H:%M:%S'), tag, msg), flush=True)


def run(cmd, t=45):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def api(cmd, wait=0.35, timeout=6):
    try:
        s = socket.create_connection((HOST, 30003), timeout=timeout)
        s.settimeout(timeout)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


# ---------- 线程 A: 30004 实时流 ----------
def stream_thread():
    while not stop.is_set():
        try:
            s = socket.create_connection((HOST, 30004), timeout=6)
            s.settimeout(6)
            w('STREAM', 'connected 30004')
            buf = b''
            while not stop.is_set():
                part = s.recv(4096)
                if not part:
                    w('STREAM', 'closed by peer')
                    break
                buf += part
                while len(buf) >= 1440:
                    pkt, buf = buf[:1440], buf[1440:]
                    mode = struct.unpack_from('<Q', pkt, 24)[0]
                    q = struct.unpack_from('<6d', pkt, 432)
                    v = struct.unpack_from('<6d', pkt, 480)
                    if not all(abs(x) < 1e6 for x in list(q) + list(v)):
                        continue
                    w('STREAM', 'mode=%d q=%s v=%s' % (
                        mode, ','.join('%+.4f' % x for x in q),
                        ','.join('%+.3f' % x for x in v)))
                time.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            w('STREAM', 'EXC %s' % e)
            time.sleep(2)


# ---------- 线程 B: API 轮询 ----------
def api_thread():
    n = 0
    while not stop.is_set():
        n += 1
        mode = api('RobotMode()')
        ang = api('GetAngle()')
        er = api('GetErrorID()')
        m = re.search(r'\{(\d+)\}', mode)
        modev = m.group(1) if m else '?'
        line = 'mode=%s ang=%s err=%s' % (modev, ang.split(',', 1)[-1][:110], er[:70])
        if n % 10 == 1:
            line += ' pose=%s' % api('GetPose()').split(',', 1)[-1][:110]
        w('API', line)
        time.sleep(0.6)


# ---------- 线程 C: HTTP SDO 0x6062/3/4 ----------
def sdo_thread():
    avail = None
    while not stop.is_set():
        for axis, slave in (('J2', 4), ('J3', 5)):
            vals = []
            for key, idx in (('addr606200', 0x6062), ('addr606300', 0x6063), ('addr606400', 0x6064)):
                body = {'body': [{'key': key, 'servoNum': axis}]}
                try:
                    req = urllib.request.Request('http://%s:22000/settings/readServoParams' % HOST,
                                                 data=json.dumps(body).encode(),
                                                 headers={'Content-Type': 'application/json'},
                                                 method='POST')
                    with urllib.request.urlopen(req, timeout=8) as r:
                        r.read()
                    if avail is None:
                        avail = True
                except Exception as e:  # noqa: BLE001
                    if avail is None:
                        avail = False
                        w('SDO', '通道不可用（%s）⇒ 只用 API+流+日志' % type(e).__name__)
                    return
                time.sleep(0.9)
            if avail:
                txt = run("grep -a 'sdo read' %s | tail -8" % LOG)
                got = {}
                for line in txt.splitlines():
                    mm = re.search(r'slave=(\d+),index=(\d+),subIndex=(\d+),value=([-\d.]+)', line)
                    if mm and 'fail' in line:
                        got[(int(mm.group(2)), int(mm.group(3)))] = mm.group(4)
                w('SDO', '%s 6062=%s 6063=%s 6064=%s'
                  % (axis, got.get((0x6062, 0), '?'), got.get((0x6063, 0), '?'), got.get((0x6064, 0), '?')))
        time.sleep(6)


w('MONITOR', '启动，输出 %s，时长 %d 秒；现在去 RoboDK 执行运动' % (OUT, DUR))
w('MONITOR', '初始: mode=%s ang=%s' % (api('RobotMode()'), api('GetAngle()')))

ths = [threading.Thread(target=stream_thread, daemon=True),
       threading.Thread(target=api_thread, daemon=True),
       threading.Thread(target=sdo_thread, daemon=True)]
for t in ths:
    t.start()
try:
    time.sleep(DUR)
except KeyboardInterrupt:
    pass
stop.set()
time.sleep(1)
w('MONITOR', '结束。日志文件: %s' % OUT)
fh.close()
