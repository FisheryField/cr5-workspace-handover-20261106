#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强版运动监控（只读）。
   线程A 30004 实时流（mode / qActual / qdActual）—— 驱动器系
   线程B API 轮询（GetAngle / RobotMode / GetErrorID / GetPose）—— 主控系
   线程C 日志尾部跟踪（PoseTrace 三列 / recv 指令 / queuedCmdIndex / 报警 / logServoError）
          ★ PoseTrace 是主控每个伺服周期打印的，含 nextPos / (PDO0x6062) / gActualPosition
            三列同一时刻的值 —— 这是"两系对照"最严谨的数据源
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
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 1800
OUT = os.path.join(r'D:\mydata\workspace', 'mon2_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
CTL_LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
lock = threading.Lock()
stop = threading.Event()
fh = open(OUT, 'w', encoding='utf-8')


def w(tag, msg):
    with lock:
        fh.write('%s [%s] %s\n' % (time.strftime('%H:%M:%S'), tag, msg))
        fh.flush()


def run(cmd, t=45):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or ''))


def api(cmd, wait=0.3, timeout=6):
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


def stream_thread():
    while not stop.is_set():
        try:
            s = socket.create_connection((HOST, 30004), timeout=6)
            s.settimeout(6)
            w('STREAM', 'connected')
            buf = b''
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
                    # 只在姿态变化或速度非零时记录，降低体积
                    w('STREAM', 'mode=%d q=%s v=%s' % (mode, ','.join('%+.4f' % x for x in q),
                                                       ','.join('%+.3f' % x for x in v)))
                time.sleep(0.12)
        except Exception as e:  # noqa: BLE001
            w('STREAM', 'EXC %s' % e)
            time.sleep(2)


def api_thread():
    n = 0
    while not stop.is_set():
        n += 1
        mode = api('RobotMode()')
        ang = api('GetAngle()')
        er = api('GetErrorID()')
        m = re.search(r'\{(\d+)\}', mode)
        w('API', 'mode=%s ang=%s err=%s%s' % (
            m.group(1) if m else '?',
            ang.split(',', 1)[-1].rstrip(';').replace('GetAngle()', '')[:100],
            er[:60],
            (' pose=' + api('GetPose()').split(',', 1)[-1][:100]) if n % 8 == 1 else ''))
        time.sleep(0.5)


def log_thread():
    line0 = int((run('wc -l < %s' % CTL_LOG).split() or ['0'])[0] or 0)
    w('LOG', 'tail 起点 = %d 行' % line0)
    pat = re.compile(r'PoseTrace: gRobotAxisMove.nextPos|PoseTrace: \(PDO0x6062\)|'
                     r'PoseTrace: gActualPosition|recv =|queuedCmdIndex|AlarmSysSetBit|'
                     r'AlarmSysClearBit|logServoError|robot enabled|robot disabled|'
                     r'calihome|HomeNumdone|gPowerDown')
    while not stop.is_set():
        time.sleep(1.5)
        try:
            out = run('tail -n +%d %s' % (line0 + 1, CTL_LOG))
        except Exception as e:  # noqa: BLE001
            w('LOG', 'EXC %s' % e)
            continue
        if not out.strip():
            continue
        for line in out.strip().splitlines():
            if pat.search(line):
                w('LOG', line.strip()[:230])
        line0 += len(out.strip().splitlines())


w('MON', '启动 输出=%s 时长=%ds' % (OUT, DUR))
w('MON', '初始 mode=%s ang=%s' % (api('RobotMode()'), api('GetAngle()')))
for t in (threading.Thread(target=stream_thread, daemon=True),
          threading.Thread(target=api_thread, daemon=True),
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
