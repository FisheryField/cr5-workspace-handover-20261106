#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验改后的 TCP真实运动_P2P版.py：
   ① 语法 ② 直发段是否已包进 try/except 并自动回退 ③ 分支结构是否完整 ④ 版本号
"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(P, encoding='utf-8').read()
print('字节数 = %d' % len(src.encode('utf-8')))
try:
    ast.parse(src)
    print('[1] 语法: PASS ✓')
except SyntaxError as e:
    print('[1] 语法: FAIL ✗ %s (line %s)' % (e.msg, e.lineno))
    sys.exit(1)

print('[2] 版本号:')
m = re.search(r"LOG_VERSION\s*=\s*'([^']+)'", src)
print('    ', m.group(1) if m else 'MISSING !!')

print('[3] 关键改动点:')
checks = [
    ('_direct_done = False', '直发标志初始化'),
    ('_direct_done = True', '直发成功置位'),
    ('except Exception as _direct_exc:', '直发失败捕获'),
    ('【v14u-fix】法兰补偿MOVL直发未成功', '回退日志'),
    ('if not _direct_done and waypoints:', '细分路径分支（回退目标）'),
    ('elif not _direct_done:', '普通分支'),
    ('v14v 提示', '外层提示已更新'),
]
for s, label in checks:
    print('    %-46s %-24s %d 次 %s' % (s[:46], label, src.count(s), 'OK' if src.count(s) else '!! 缺失'))

print('[4] 旧文本应已消失:')
for s in ('建议去勾回退', 'v14u-20261013-1059'):
    n = src.count(s)
    print('    %-30s %d 次 %s' % (s, n, 'OK（已移除）' if n == 0 else '!! 仍在'))

print('[5] 结构核查（直发块内 try/finally 与验收是否都在 _direct_done 保护下）:')
lines = src.splitlines()
# 找 "if (movl_direct and seg_mm is not None" 的行号
start = next((i for i, l in enumerate(lines, 1) if 'movl_direct and seg_mm is not None' in l), None)
endif = next((i for i, l in enumerate(lines, 1)
              if i > (start or 0) and l.strip().startswith('if not _direct_done and waypoints:')), None)
print('    直发块起始行 =', start, ' 细分分支行 =', endif)
if start and endif:
    blk = '\n'.join(lines[start - 1:endif - 1])
    for s in ('try:', 'except Exception as _direct_exc:', 'finally:', 'robot.setPoseTool(_saved_tool_pose)',
              '_movl_flange_accept', '_require_joints(step'):
        print('      块内 %-42s %d 次' % (s, blk.count(s)))

print('')
print('[6] 直发块长度 = %d 行' % ((endif - start) if (start and endif) else -1))
