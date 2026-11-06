#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监视器 v4：只用两个"互不干扰"的源，绝不碰 30003（避免抢 RoboDK 的连接）。
   STREAM 30004 实时流：mode / qActual（驱动器系）/ qdActual —— 唯一高频真值源
   LOG    控制器日志 tail -n 800（每周期重读 + 内容去重，抗日志轮转）
          ★ PoseTrace 三列 / recv 运动指令 / queuedCmdIndex / 报警 / logServoError / 使能
"""
import os
import re
import socket
import struct
import subprocess
import sys
import threading
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 2400
OUT = os.path.join(r'D:\mydata\workspace', 'mon4_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
CTL_LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
lock = threading.Lock()
stop = threading.Event()
fh = open(OUT, 'w', encoding='utf-8')


def w(tag, msg):
    with lock:
        fh.write('%s [%s] %s\n' % (time.strftime('%H:%M:%S'), tag, msg))
        fh.flush()


def run(cmd, t=25):
    try:
        r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                           stdin=subprocess.DEVNULL)
        return ((r.stdout or '') + (r.stderr or ''))
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


def stream_thread():
    while not stop.is_set():
        try:
            s = socket.create_connection((HOST, 30004), timeout=6)
            s.settimeout(6)
            w('STREAM', 'connected')
            buf = b''
            last = None
            while not stop.is_set():
                part = s.recv(8192)
                if not part:
                    break
                buf += part
                while len(buf) >= 1440:
                    pkt, buf = buf[:1440], buf[1440:]
                    mode = struct.unpack_from('<Q', pkt, 24)[0]
                    q = struct.unpack_from('<6d', pkt, 432)
                    v = struct.unpack_from('<6d', pkt, 480)
                    if not all(abs(x) < 1e6 for x in list(q) + list(v)):
                        continue
                    key = (mode, tuple(round(x, 3) for x in q), tuple(round(x, 1) for x in v))
                    if key != last:
                        w('STREAM', 'mode=%d q=%s v=%s' % (
                            mode, ','.join('%+.4f' % x for x in q),
                            ','.join('%+.2f' % x for x in v)))
                        last = key
                time.sleep(0.05)
        except Exception as e:  # noqa: BLE001
            w('STREAM', 'EXC %s' % e)
            time.sleep(2)


def log_thread():
    pat = re.compile(r'PoseTrace:|recv = .*Mov|queuedCmdIndex|AlarmSysSetBit|AlarmSysClearBit|'
                     r'logServoError|robot enabled|robot disabled|calihome|HomeNumdone|'
                     r'gPowerDown|monitorServoUptime|exist an error|SteadyError Calc')
    seen = set()
    while not stop.is_set():
        out = run('tail -n 800 %s' % CTL_LOG)
        n = 0
        for line in out.splitlines():
            s = line.strip()
            if not s or not pat.search(s):
                continue
            h = hash(s)
            if h in seen:
                continue
            seen.add(h)
            if len(seen) > 60000:
                seen.clear()
            w('LOG', s[:235])
            n += 1
        time.sleep(1.5)


w('MON', 'v4 启动（只读、不碰30003）输出=%s 时长=%ds' % (OUT, DUR))
for t in (threading.Thread(target=stream_thread, daemon=True),
          threading.Thread(target=log_thread, daemon=True)):
    t.start()
try:
    for _ in range(DUR):
        if stop.is_set():
            break
        time.sleep(1)
except KeyboardInterrupt:
    pass
stop.set()
time.sleep(1)
w('MON', '结束')
fh.close()
