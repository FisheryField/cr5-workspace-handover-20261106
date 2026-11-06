#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监视器 v5：**只用 SSH 读控制器日志**，绝不占用 30003/30004（零干扰）。
   抓：PoseTrace 三列 / recv 运动指令 / queuedCmdIndex / 报警 / logServoError /
       SteadyError 判定与阈值 / 使能与下电 / calihome
"""
import os
import re
import subprocess
import sys
import threading
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 2400
OUT = os.path.join(r'D:\mydata\workspace', 'mon5_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
CTL_LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
PAT = re.compile(
    r'PoseTrace: gRobotAxisMove\.nextPos|PoseTrace: \(PDO0x6062\)|PoseTrace: gActualPosition'
    r'|recv = .*Mov|queuedCmdIndex|AlarmSysSetBit|AlarmSysClearBit|logServoError'
    r'|robot enabled|robot disabled|calihome|HomeNumdone|gPowerDown'
    r'|SteadyError isErr|SteadyError Calc|SteadyError Threshold'
    r'|exist an error|monitorErrorStatus|disconnect was detected')
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


w('MON', 'v5（仅 SSH 读日志，零端口占用）输出=%s 时长=%ds' % (OUT, DUR))
seen = set()
n = 0
while not stop.is_set() and n < DUR // 2:
    n += 1
    out = run('tail -n 1200 %s' % CTL_LOG)
    for line in out.splitlines():
        s = line.strip()
        if not s or not PAT.search(s):
            continue
        h = hash(s)
        if h in seen:
            continue
        seen.add(h)
        if len(seen) > 80000:
            seen.clear()
        w('LOG', s[:240])
    time.sleep(2)
w('MON', '结束')
fh.close()
