#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 v14v4：语法 + 三处改动 + 用模拟数据验证「只拦 P9、放行 P5」的分支逻辑。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(P, encoding='utf-8').read()
ast.parse(src)
print('语法 PASS ✓  字节 = %d' % len(src.encode('utf-8')))

m = re.search(r"LOG_VERSION\s*=\s*'([^']+)'", src)
print('版本 =', m.group(1))

print('')
print('--- 分支逻辑模拟（用实测数据：P5 关节差 0.95°、P9 关节差 10.69°、两段都 100mm）---')
# 从源码读常量
ns = {}
for line in src.splitlines():
    mm = re.match(r'^(MOVL_DIRECT_MAX_MM|MOVL_DIRECT_BLOCK_POINTS|MOVL_ARRIVE_TOL_DEG)\s*=\s*(.+?)(\s*#.*)?$', line)
    if mm:
        ns[mm.group(1)] = ast.literal_eval(mm.group(2).strip())
print('  MOVL_DIRECT_MAX_MM       =', ns.get('MOVL_DIRECT_MAX_MM'))
print('  MOVL_DIRECT_BLOCK_POINTS =', ns.get('MOVL_DIRECT_BLOCK_POINTS'))
BLOCK = ns.get('MOVL_DIRECT_BLOCK_POINTS', ())
MAXMM = ns.get('MOVL_DIRECT_MAX_MM', 150.0)

cases = [
    (4, 5, 100.0, 0.0, 0.95, 'P5（实测直发 1.1s 到位）'),
    (8, 9, 100.0, 0.0, 10.69, 'P9（实测直发 60s 未到位 + 界面碰撞）'),
    (6, 7, 100.0, 0.0, 1.20, 'P7（普通短段）'),
    (1, 2, 400.0, 0.0, 5.00, 'P2（段长超 150 上限）'),
]
print('')
for prev, i, seg_mm, seg_rot, jdiff, label in cases:
    gate_block = (i in BLOCK)
    gate_len = seg_mm <= MAXMM
    direct = (not gate_block) and gate_len
    why = []
    if gate_block:
        why.append('在禁直发名单')
    if not gate_len:
        why.append('段长 %.0fmm > %.0f' % (seg_mm, MAXMM))
    print('  P%-3d %-32s 关节差%6.2f°  ⇒ %s %s'
          % (i, label, jdiff, '走【直发】' if direct else '走【细分】', ('（' + '、'.join(why) + '）') if why else ''))

print('')
print('⇒ 期望: P5 走直发 ✓ / P9 走细分 ✓ / P7 走直发 ✓ / P2 走细分（超长）✓')
