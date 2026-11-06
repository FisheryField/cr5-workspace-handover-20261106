#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对测试 GUI 脚本的关键点。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\测试_原点P1P2_单步.py'
s = io.open(P, encoding='utf-8').read()
print('文件行数 =', s.count(chr(10)) + 1)
print('')

checks = [
    ('SEG_DELAY = 2.0', SEG := ('SEG_DELAY = 2.0' in s)),
    ('每段运动前延时：time.sleep(SEG_DELAY) 恰好 2 次', s.count('time.sleep(SEG_DELAY)') == 2),
    ('用 SimulatorJoints，且不出现 robot.Joints()', ('SimulatorJoints' in s) and ('robot.Joints()' not in s)),
    ('30004 只读反馈函数存在', ('def _controller_feedback' in s) and ('30004' in s)),
    ('StoppedError 兜底存在', ('StoppedError' in s) and ('Robot not connected' in s)),
    ('三次反馈确认（range(3)）', 'for sample in range(3)' in s),
    ('三段 MoveJ（原点/P1/P2）', len(re.findall(r'_move_one\("MoveJ"', s)) == 3),
    ('无 EnableRobot/DisableRobot/ClearError/setCollide',
     not any(k in s for k in ('EnableRobot(', 'DisableRobot(', 'ClearError(', 'setCollide'))),
    ('三段目标串出现（ORIGIN/P1/P2）', all(k in s for k in ('_move_one("MoveJ", ORIGIN', '_move_one("MoveJ", P1', '_move_one("MoveJ", P2'))),
]
for name, ok in checks:
    print('  %-52s %s' % (name, '✓' if ok else '✗'))

print('')
for key in ('ORIGIN = [', 'P1 = [', 'P2 = ['):
    m = re.search(re.escape(key) + '[^' + chr(10) + ']*', s)
    print('  ' + (m.group(0) if m else ('缺 ' + key)))
