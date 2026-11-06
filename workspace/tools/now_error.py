#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""当下状态：模式 / 报警 / 姿态 + 日志里最新的报警与错误。"""
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


def api(cmd, wait=0.9):
    try:
        s = socket.create_connection((HOST, 30003), timeout=8)
        s.settimeout(6)
        s.sendall((cmd + '\n').encode())
        time.sleep(wait)
        d = s.recv(8192).decode('utf-8', 'replace')
        s.close()
        return d.strip().replace('\n', ' ')
    except Exception as e:  # noqa: BLE001
        return 'EXC %s' % e


print('=== 当下 API ===')
print('RobotMode  : %s' % api('RobotMode()'))
print('GetErrorID : %s' % api('GetErrorID()'))
print('GetAngle   : %s' % api('GetAngle()'))
print('')
print('=== 日志里最近的报警置位/清除 ===')
print(run("grep -a 'AlarmSysSetBit\\|AlarmSysClearBit' %s | tail -8 | cut -c1-120" % L))
print('')
print('=== 最近的稳态误差判定 ===')
print(run("grep -a 'SteadyError' %s | tail -6 | cut -c1-175" % L))
print('')
print('=== 最近 12 行原始日志 ===')
print(run("tail -12 %s | cut -c1-170" % L))
