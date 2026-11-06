#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查报警 130 (0x82) 通用IO板掉线 的含义与处置。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\alarm_controller.json'
raw = io.open(P, encoding='utf-8').read()
d = json.loads(raw)
print('文件顶层类型:', type(d).__name__)
if isinstance(d, dict):
    ks = list(d.keys())
    print('键数量:', len(ks), ' 前 5 个:', ks[:5])
    print('')
    for k in ('130', '0x82', '82', '118', '121', '126', '99'):
        if k in d:
            print('  [%s] %s' % (k, json.dumps(d[k], ensure_ascii=False)[:400]))
else:
    print('列表长度:', len(d))
    print('首元素示例:', json.dumps(d[0], ensure_ascii=False)[:300])
    for it in d:
        s = json.dumps(it, ensure_ascii=False)
        if '"130"' in s or '"0x82"' in s or '"118"' in s or '"126"' in s:
            print('  ', s[:400])
