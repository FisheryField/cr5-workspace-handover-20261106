#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查：RoboDK 的 TCP 运动脚本发来"全 0"目标后为何不动。
   抓：最近的 TCP 命令、运动队列条目、是否判定为完成、当前姿态。"""
import re
import socket
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd'
L = '/dobot/userdata/CR5_sys_files/project/logs/all/log'


def run(cmd, t=60):
    r = subprocess.run([RSH, cmd], capture_output=True, text=True, timeout=t,
                       stdin=subprocess.DEVNULL)
    return ((r.stdout or '') + (r.stderr or '')).strip()


def api(cmd):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(0.9)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


print('=== 当前状态（只读）===')
print('RobotMode  : %s' % api('RobotMode()'))
print('GetAngle   : %s' % api('GetAngle()'))
print('GetErrorID : %s' % api('GetErrorID()')[:110])
print('')
print('=== 最近的 TCP 命令（recv =）===')
print(run("grep -a 'recv =' %s | tail -18 | cut -c1-165" % L))
print('')
print('=== 最近的运动队列/规划相关行 ===')
print(run("grep -a 'queuedCmdIndex\\|JointMovJ\\|MOVJPreDeal\\|movj finsh\\|PreDealData' %s | tail -16 | cut -c1-175" % L))
print('')
print('=== 最近 3 分钟内是否有任何运动/报警 ===')
print(run("grep -a 'AlarmSysSetBit\\|robot enabled\\|robot disabled\\|MovJ\\|MovL\\|Arc' %s | tail -8 | cut -c1-150" % L))
