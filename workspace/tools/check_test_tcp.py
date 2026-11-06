#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对 TCP 版 test.py 的关键点。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
s = io.open(P, encoding='utf-8').read()
print('行数 =', s.count(chr(10)) + 1)
print('')
checks = [
    ('P1/P2 走 fanuc_to_pose（TCP 目标）', 'fanuc_to_pose(*vals)' in s),
    ('单点可达性：SolveIK + _tcp_target_to_flange', 'def check_point' in s and '_tcp_target_to_flange' in s),
    ('段间 TCP 采样检查（SAMPLES=20）', 'def check_segment_tcp' in s and 'SAMPLES = 20' in s),
    ('段间关节空间检查：MoveJ_Test', 'def check_segment_joint' in s and 'MoveJ_Test' in s),
    ('预检在仿真模式（RUNMODE_SIMULATE）', 'RDK.setRunMode(RUNMODE_SIMULATE)' in s),
    ('预检不通过则不发送运动', '可达性预检未通过，未发送任何运动指令' in s),
    ('两段各延时 2 秒（sleep(SEG_DELAY) 恰好 2 次）', s.count('time.sleep(SEG_DELAY)') == 2),
    ('单步调用照抄 execute_joint_target', s.count('robot.MoveJ(target)') == 1),
    ('无 30004 / 无 StoppedError 兜底 / 无 Busy / 无 setPoseFrame',
     not any(k in s for k in ('30004', 'except StoppedError', 'robot.Busy(', 'setPoseFrame('))),
    ('日志原文关节值在文件里', '16.379607, -6.735621, -111.802214' in s and '-77.933681, -57.346998' in s),
]
for name, ok in checks:
    print('  %-52s %s' % (name, '✓' if ok else '✗'))
