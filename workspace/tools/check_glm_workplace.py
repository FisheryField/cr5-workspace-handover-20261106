#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核验 glm-workplace 是否自包含、可交接。"""
import ast
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
G = r'D:\mydata\glm-workplace'
print('目录 =', G)
print('')

# 1) README 里提到的文件是否都存在（递归查找，因为有些在 data/ tools/ 子目录）
readme = io.open(os.path.join(G, 'README.md'), encoding='utf-8').read()
mentioned = re.findall(r'`([^`]+\.(?:md|py|json|bin|txt))`', readme)
print('--- README 引用的文件（递归查找）---')
missing = []
# 先把目录下所有文件名收集一份
allnames = {}
for root, _dirs, files in os.walk(G):
    for f in files:
        allnames.setdefault(f, os.path.join(root, f))
for m in sorted(set(mentioned)):
    base = os.path.basename(m)
    p = os.path.join(G, m)
    if not os.path.exists(p):
        p = allnames.get(base)          # 递归兜底
    ok = bool(p)
    if not ok:
        missing.append(m)
    print('  %-34s %-38s %s' % (m, ('-> ' + p.replace(G, '.')) if ok else '', 'OK' if ok else 'MISSING !!'))
print('')

# 2) 目录清单
print('--- 实际文件 ---')
total = 0
for root, _dirs, files in os.walk(G):
    for f in sorted(files):
        p = os.path.join(root, f)
        total += 1
        print('  %-46s %8d' % (p.replace(G, '.'), os.path.getsize(p)))
print('  共 %d 个文件' % total)
print('')

# 3) test.py 的常量与结构
tp = os.path.join(G, 'test.py')
src = io.open(tp, encoding='utf-8').read()
ast.parse(src)
print('--- test.py 核验 ---')
print('  语法 = PASS   字节数 = %d' % len(src.encode('utf-8')))
for n in ('ROBOT_SPEED', 'SEG_DELAY', 'P4_J6_DELTA', 'P8_J6_DELTA'):
    m = re.search(r'^%s\s*=\s*([\d.]+)' % n, src, re.M)
    print('  %-14s = %s' % (n, m.group(1) if m else 'MISSING !!'))
n_pt = len(re.findall(r'^P\d+_TCP\s*=', src, re.M))
n_seg = len(re.findall(r'^# ---- 段 \d+ / \d+', src, re.M))
print('  点常量 P*_TCP  = %d 个' % n_pt)
print('  段块           = %d 个' % n_seg)
print('  ITEM_TYPE_TOOL = %d（应=1，仅注释）' % src.count('ITEM_TYPE_TOOL'))
print('')

# 4) 工具可编译
print('--- tools/ 里的 .py 可编译性 ---')
tdir = os.path.join(G, 'tools')
for f in sorted(os.listdir(tdir)):
    if not f.endswith('.py'):
        continue
    p = os.path.join(tdir, f)
    try:
        ast.parse(io.open(p, encoding='utf-8').read())
        print('  %-32s OK' % f)
    except SyntaxError as e:
        print('  %-32s !! %s' % (f, e))
print('')

# 5) 关键数据文件可解析
print('--- data/ 里的 json 可解析性 ---')
import json
ddir = os.path.join(G, 'data')
for f in sorted(os.listdir(ddir)):
    if not f.endswith('.json'):
        continue
    p = os.path.join(ddir, f)
    try:
        d = json.loads(io.open(p, encoding='utf-8', errors='replace').read())
        n = len(d) if hasattr(d, '__len__') else '?'
        print('  %-30s OK（%s 项）' % (f, n))
    except Exception as e:  # noqa: BLE001
        print('  %-30s !! %s' % (f, e))

print('')
print('缺失引用: %s' % ('无 ✓' if not missing else ', '.join(missing)))
