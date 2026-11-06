#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查刚才 RoboDK 从原点出发的 TCP 运动：命令、队列、返回码、姿态变化、报警。"""
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


print('=== 现在（只读）===')
print('RobotMode  : %s' % api('RobotMode()'))
print('GetAngle   : %s' % api('GetAngle()'))
print('GetPose    : %s' % api('GetPose()'))
print('GetErrorID : %s' % api('GetErrorID()')[:110])
print('')
print('=== 最近的 TCP 命令（含运动指令）===')
print(run("grep -a 'recv =' %s | tail -30 | cut -c1-180" % L))
print('')
print('=== 运动指令/队列/规划/完成 ===')
print(run("grep -a 'JointMovJ\\|MovJ(\\|MovL(\\|queuedCmdIndex\\|movj finsh\\|movl finsh\\|PreDealDataRunning\\|ret = .*func' %s | tail -22 | cut -c1-180" % L))
print('')
print('=== 报警 / 伺服错误 ===')
print(run("grep -a 'AlarmSysSetBit\\|logServoError\\|exist an error' %s | tail -8 | cut -c1-160" % L))
