#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读当前报警与最近的运动/报警/伺服错误日志。"""
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


print('=== 当前状态 ===')
print('RobotMode  : %s' % api('RobotMode()'))
print('GetErrorID : %s' % api('GetErrorID()'))
print('GetAngle   : %s' % api('GetAngle()'))
print('')
print('=== 最近的报警位 ===')
print(run("grep -a 'AlarmSysSetBit\\|AlarmSysClearBit' %s | tail -12 | cut -c1-140" % L))
print('')
print('=== 最近的伺服错误 / 使能被拒 ===')
print(run("grep -a 'logServoError\\|exist an error\\|servo.*error\\|can.t enable' %s | tail -10 | cut -c1-170" % L))
print('')
print('=== 最近的运动指令与结果 ===')
print(run("grep -a 'recv = .*Mov\\|queuedCmdIndex\\|JointMovJ\\|ret = .*func\\|move.*fail\\|Fail\\|error' %s | tail -20 | cut -c1-175" % L))
print('')
print('=== 最近 20 行原始日志 ===')
print(run("tail -20 %s | cut -c1-175" % L))
