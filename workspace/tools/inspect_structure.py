#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看清 structure.json 的结构：limits 挂在哪一层。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\structure_orig.json'
d = json.loads(io.open(P, encoding='utf-8').read())
print('顶层键 =', list(d.keys()))
print('')


def walk(o, path='', depth=0):
    if depth > 4:
        return
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'limits' or (isinstance(v, (dict, list)) and 'limit' in k.lower()):
                print('  %s/%s  ->  %s' % (path, k, json.dumps(v, ensure_ascii=False)[:220]))
            walk(v, path + '/' + str(k), depth + 1)
    elif isinstance(o, list):
        for i, v in enumerate(o[:3]):
            walk(v, path + '[%d]' % i, depth + 1)


print('--- 含 limits 的路径 ---')
walk(d)

print('')
print('--- 顶层各键的类型 ---')
for k, v in d.items():
    t = type(v).__name__
    n = len(v) if hasattr(v, '__len__') else ''
    print('  %-24s %-6s %s' % (k, t, n))
    if isinstance(v, dict):
        print('      子键:', list(v.keys())[:12])

print('')
print('--- 原始文本里 limits 附近的上下文 ---')
raw = io.open(P, encoding='utf-8').read()
i = raw.find('"limits"')
print(raw[max(0, i - 300):i + 400] if i >= 0 else '(未找到)')
