#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""去掉注释与文档字符串后，只查 test.py 的**代码**。"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py'
src = io.open(P, encoding='utf-8').read()

tree = ast.parse(src)
# 去掉所有 docstring 节点，再反编译回源码文本
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            node.body.pop(0)
code = ast.unparse(tree)

print('代码字符数（不含注释/docstring） =', len(code))
print('')
checks = [
    ('30004', '30004'),
    ('_controller_feedback', '_controller_feedback'),
    ('except StoppedError', 'except StoppedError'),
    ('robot.Busy(', 'robot.Busy('),
    ('setPoseFrame(', 'setPoseFrame('),
    ('setPoseTool(', 'setPoseTool('),
    ('robot.Joints()', 'robot.Joints()'),
    ('socket', 'socket'),
]
for name, pat in checks:
    print('  代码中出现 %-24s %s' % (name, '✗ 有（不该有）' if pat in code else '✓ 无'))
print('')
print('  代码中 robot.MoveJ( 次数 =', code.count('robot.MoveJ('))
print('  代码中 time.sleep(SEG_DELAY) 次数 =', code.count('time.sleep(SEG_DELAY)'))
print('  代码中 SolveIK 次数 =', code.count('SolveIK'))
print('  代码中 MoveJ_Test 次数 =', code.count('MoveJ_Test'))
print('  代码中 setRunMode(RUNMODE_SIMULATE) 次数 =', code.count('setRunMode(RUNMODE_SIMULATE)'))
print('  代码中 setRunMode(RUNMODE_RUN_ROBOT) 次数 =', code.count('setRunMode(RUNMODE_RUN_ROBOT)'))
