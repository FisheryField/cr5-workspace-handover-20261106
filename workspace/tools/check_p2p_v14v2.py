#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 v14v2：语法 + 新常量 + 无进展早退逻辑 + 版本号。"""
import ast
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(P, encoding='utf-8').read()
print('字节数 = %d' % len(src.encode('utf-8')))
ast.parse(src)
print('[1] 语法 PASS ✓')

m = re.search(r"LOG_VERSION\s*=\s*'([^']+)'", src)
print('[2] 版本 =', m.group(1) if m else 'MISSING')

print('[3] 常量:')
for n in ('MOVL_ARRIVE_WAIT_S', 'MOVL_STUCK_S', 'MOVL_STUCK_TOL_DEG', 'MOVL_ARRIVE_TOL_DEG'):
    mm = re.search(r'^%s\s*=\s*([\d.]+)' % n, src, re.M)
    print('    %-22s = %s' % (n, mm.group(1) if mm else 'MISSING !!'))

print('[4] 无进展早退逻辑:')
for s in ('best_err = None', 'stuck_since = None',
          'err < best_err - MOVL_STUCK_TOL_DEG',
          'time.time() - stuck_since >= MOVL_STUCK_S',
          'MovL 直发【无进展】'):
    print('    %-46s %d 次 %s' % (s[:46], src.count(s), 'OK' if src.count(s) else '!! 缺失'))

print('[5] 自动回退仍在:')
for s in ('_direct_done', '【v14u-fix】', 'if not _direct_done and waypoints:'):
    print('    %-46s %d 次 %s' % (s[:46], src.count(s), 'OK' if src.count(s) else '!! 缺失'))

print('[6] 语法/作用域自检（函数在常量之前定义，调用在运行期解析全局名 → 合法）:')
lines = src.splitlines()
fn = next(i for i, l in enumerate(lines, 1) if l.startswith('def _wait_arrival_then_static'))
c1 = next(i for i, l in enumerate(lines, 1) if l.startswith('MOVL_STUCK_S'))
c2 = next(i for i, l in enumerate(lines, 1) if l.startswith('MOVL_ARRIVE_WAIT_S'))
print('    函数 L%d，MOVL_STUCK_S L%d，MOVL_ARRIVE_WAIT_S L%d' % (fn, c1, c2))
print('    ⇒ %s' % ('OK（都在模块级，调用时可解析）✓' if c1 > fn and c2 > fn else '需检查'))

print('[7] 模拟无进展早退判定（纯逻辑推演，不连机器人）:')
MOVL_STUCK_S, MOVL_STUCK_TOL_DEG, MOVL_ARRIVE_TOL_DEG = 10.0, 0.05, 2.0


def sim(series, label):
    best = None
    stuck = None
    for t, err in series:
        if err <= MOVL_ARRIVE_TOL_DEG:
            print('    %-26s t=%-5.1f 到位 ✓' % (label, t))
            return
        if best is None or err < best - MOVL_STUCK_TOL_DEG:
            best, stuck = err, t
        elif stuck is not None and t - stuck >= MOVL_STUCK_S:
            print('    %-26s t=%-5.1f ✗ 无进展早退（稳定在 %.2f°）⇒ 回退细分' % (label, t, err))
            return
    print('    %-26s 序列结束（未触发）' % label)


# P9 实测：从 5s 到 58s 稳定 10.69
sim([(t, 10.69) for t in (0, 2, 5, 8, 10, 12, 15, 20)], 'P9 实测（零变化）')
# P5 实测：1.1s 到位
sim([(0, 10.0), (0.5, 3.0), (1.0, 0.95)], 'P5 实测（1.1s）')
# 慢启动假设：8s 后才开始动
sim([(0, 12.0), (4, 12.0), (8, 11.0), (9, 6.0), (10, 0.5)], '慢启动（8s 后动起来）')
# 极慢但持续改善：不应误杀
sim([(t, 12.0 - 0.3 * t) for t in (0, 3, 6, 9, 12, 15)], '持续缓动（不会误杀）')
