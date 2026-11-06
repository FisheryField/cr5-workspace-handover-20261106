#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯日志监视（不轮询，避免污染日志）：看 RoboDK 是否连上 30003、是否发出指令。
   用法: python tools/watch_conn_only.py [秒数]
"""
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 150
PAT = (r'accepted an new connection|conn_req_dir|recv =|queuedCmdIndex|'
       r'AlarmSysSetBit|logServoError|robot enabled|robot disabled|finsh')


def run(cmd, t=30):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


line0 = int(run('wc -l < %s' % L).split()[0])
print('baseline = %d 行；监视 %d 秒（请现在去 RoboDK：右键机器人 → Connect，勾上 Run on robot，再运行程序）'
      % (line0, DUR))
t0 = time.time()
while time.time() - t0 < DUR:
    time.sleep(2.5)
    out = run('tail -n +%d %s' % (line0 + 1, L))
    if not out.strip():
        continue
    n = len(out.strip().splitlines())
    line0 += n
    for line in out.strip().splitlines():
        if re.search(PAT, line):
            print('[%5.1fs] %s' % (time.time() - t0, line.strip()[:170]))
print('\n监视结束。')
