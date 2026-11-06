#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重跑 mon2 分析（过滤掉自己的轮询噪音），并检查轮转日志里的运动指令。"""
import glob
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
files = sorted(glob.glob(r'D:\mydata\workspace\mon2_*.log'), key=os.path.getmtime)
path = files[-1]
NOISE = re.compile(r'GetAngle\(\)|GetErrorID\(\)|RobotMode\(\)|GetPose\(\)|'
                   r'ClearError\(\)|DisableRobot\(\)|EnableRobot\(\)|SpeedFactor')
MOTION = re.compile(r'MovJ|MovL|queuedCmdIndex|AlarmSysSetBit|AlarmSysClearBit|logServoError|'
                    r'robot enabled|robot disabled|gPowerDown|calihome|HomeNumdone|OnPTPCmd')

print('=== 文件: %s ===' % os.path.basename(path))
print('')
print('=== A) 监视窗口内的运动/报警类日志行 ===')
n = 0
for line in open(path, encoding='utf-8', errors='replace'):
    m = re.match(r'(\d\d:\d\d:\d\d) \[LOG\] (.*)', line)
    if m and MOTION.search(m.group(2)) and not NOISE.search(m.group(2)):
        print('  %s  %s' % (m.group(1), m.group(2)[:185]))
        n += 1
print('  （共 %d 条）' % n)

print('')
print('=== B) PoseTrace 三列的 J2 轨迹（每个变化点，阈值 0.05°）===')
cur = {}
prev = {}
for line in open(path, encoding='utf-8', errors='replace'):
    m = re.match(r'(\d\d:\d\d:\d\d) \[LOG\] (.*PoseTrace.*)', line)
    if not m:
        continue
    t, r = m.group(1), m.group(2)
    kind = 'next' if 'nextPos' in r else ('dem' if '0x6062' in r else ('act' if 'gActualPosition' in r else None))
    if not kind:
        continue
    mm = re.search(r':\s*([-0-9.,\s]+)\s*$', r.strip())
    try:
        v = [float(x) for x in mm.group(1).strip().rstrip(',').split(',')] if mm else None
    except ValueError:
        v = None
    if not v or len(v) < 6:
        continue
    j2 = v[1]
    if kind not in prev or abs(j2 - prev[kind]) > 0.05:
        print('  %s  %-4s J2 = %+9.4f   (全六轴: %s)' % (t, kind, j2, ','.join('%+.3f' % x for x in v)))
        prev[kind] = j2

print('')
print('=== C) 轮转日志里的运动指令（控制器侧权威）===')
r = subprocess.run([r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd',
                    "cd /dobot/userdata/CR5_sys_files/project/logs/all && "
                    "ls -la log log.1 | head -4 && echo '--- Mov 指令 ---' && "
                    "grep -a 'recv = .*Mov' log log.1 log.2 2>/dev/null | tail -15 | cut -c1-190 && "
                    "echo '--- 队列 ---' && grep -a 'queuedCmdIndex' log log.1 log.2 2>/dev/null | tail -8 | cut -c1-190 && "
                    "echo '--- 报警 ---' && grep -a 'AlarmSysSetBit\\|logServoError' log log.1 2>/dev/null | tail -6 | cut -c1-150"],
                   capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
print(r.stdout.strip() or '(空)')
