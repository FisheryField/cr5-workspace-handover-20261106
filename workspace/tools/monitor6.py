#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监视器 v6：走 paramiko（rsh.cmd 已被系统清理），只读控制器日志，绝不碰 30003/30004。
   抓：PoseTrace 三列 / recv 运动指令 / queuedCmdIndex / 报警 / logServoError /
       robot enabled|disabled / gPowerDown / SteadyError。
"""
import os
import re
import sys
import threading
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HOST = '192.168.5.1'
USER = 'root'
PASS = 'dobot'
CTL_LOG = '/dobot/userdata/CR5_sys_files/project/logs/all/log'
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 2400
OUT = os.path.join(r'D:\mydata\workspace', 'mon6_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
PAT = re.compile(
    r'PoseTrace: gRobotAxisMove\.nextPos|PoseTrace: \(PDO0x6062\)|PoseTrace: gActualPosition'
    r'|recv = .*Mov|queuedCmdIndex|AlarmSysSetBit|AlarmSysClearBit|logServoError'
    r'|robot enabled|robot disabled|calihome|HomeNumdone|gPowerDown'
    r'|SteadyError isErr|SteadyError Calc|exist an error|monitorServoUptime')

fh = open(OUT, 'w', encoding='utf-8')
lock = threading.Lock()


def w(tag, msg):
    with lock:
        fh.write('%s [%s] %s\n' % (time.strftime('%H:%M:%S'), tag, msg))
        fh.flush()


def main():
    import paramiko
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, password=PASS, timeout=15,
                allow_agent=False, look_for_keys=False)
    w('MON', 'v6(paramiko) 输出=%s 时长=%ds' % (OUT, DUR))
    seen = set()
    n = 0
    while n < DUR // 2:
        n += 1
        try:
            _in, out, _err = cli.exec_command('tail -n 1500 %s' % CTL_LOG, timeout=30)
            text = out.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001
            w('MON', 'SSH EXC %s' % e)
            time.sleep(3)
            continue
        for line in text.splitlines():
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
    cli.close()


if __name__ == '__main__':
    main()
