#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查改写后的 test.py：语法、关键函数、关键调用点、危险调用（RUN_ROBOT 下用 Joints 等）。"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()
print('文件字节数 =', len(src.encode('utf-8')))

# 1) 语法
try:
    tree = ast.parse(src)
    print('[1] 语法检查: PASS')
except SyntaxError as e:
    print('[1] 语法检查: FAIL  %s (line %s)' % (e.msg, e.lineno))
    sys.exit(1)

# 2) 关键定义
funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
wanted = ['_enable_obstacle_checks', '_check_segment', '_collision_details',
          '_movej_test_cached', '_cache_key_joints', '_solve_ik_joints',
          '_do_segment_check', '_move_one', '_worker', 'fanuc_to_pose']
print('[2] 关键函数:')
for w in wanted:
    print('    %-26s %s' % (w, 'OK' if w in funcs else 'MISSING !!'))

# 3) 关键字符串/调用点出现次数
checks = [
    ("'安装台_650x650x80mm'", "台面障碍物"),
    ("'地面_禁止穿越'", "地面障碍物"),
    ('setCollisionActivePair', '碰撞对配置'),
    ('setCollisionActive(', '启用碰撞检测'),
    ('MoveJ_Test', 'MoveJ 路径碰撞测试'),
    ('RUNMODE_SIMULATE', '仿真模式（检测需要）'),
    ('RUNMODE_RUN_ROBOT', '真机模式'),
    ('SolveIK', '位姿→关节逆解'),
    ('CollisionPairs', '碰撞详情'),
]
print('[3] 关键调用点:')
for s, label in checks:
    print('    %-34s %-22s 出现 %d 次' % (s, label, src.count(s)))

# 4) 危险核查：末端工具那段不能出现
print('[4] 末端工具（按要求应省略）:')
print('    ITEM_TYPE_TOOL 出现 %d 次  %s' % (src.count('ITEM_TYPE_TOOL'),
      'OK（已省略）' if src.count('ITEM_TYPE_TOOL') == 0 else '!! 仍然存在'))
print('    磨砂/圆盘 出现 %d 次  %s' % (src.count('磨砂') + src.count('圆盘'),
      'OK（未涉及）' if (src.count('磨砂') + src.count('圆盘')) == 0 else '!! 出现'))

# 5) 检测是否真的插在两段运动之前
print('[5] 调用顺序（按行号）:')
lines = src.splitlines()
marks = []
for i, ln in enumerate(lines, 1):
    if '_do_segment_check(' in ln and 'def ' not in ln:
        marks.append((i, '碰撞检测调用: ' + ln.strip()[:70]))
    if '_move_one(' in ln and 'def ' not in ln:
        marks.append((i, '运动调用:     ' + ln.strip()[:70]))
for i, t in sorted(marks):
    print('    L%-5d %s' % (i, t))
