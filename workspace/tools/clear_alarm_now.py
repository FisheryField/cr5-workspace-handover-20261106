#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清报警：ClearError() -> 复查 RobotMode / GetErrorID。"""
import re
import socket
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'


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


print('清前 : RobotMode=%s' % api('RobotMode()'))
print('       GetErrorID=%s' % api('GetErrorID()'))
print('')
print('ClearError() -> %s' % api('ClearError()', wait=1.5))
time.sleep(2)
print('')
print('清后 : RobotMode=%s' % api('RobotMode()'))
print('       GetErrorID=%s' % api('GetErrorID()'))
time.sleep(2)
print('再查 : RobotMode=%s' % api('RobotMode()'))
print('       GetErrorID=%s' % api('GetErrorID()'))
