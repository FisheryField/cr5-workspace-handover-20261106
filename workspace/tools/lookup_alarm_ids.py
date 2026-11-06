#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查报警含义（表是 list，id 是 int）。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = json.loads(io.open(r'D:\mydata\workspace\data\alarm_controller.json', encoding='utf-8').read())
by_id = {int(it['id']): it for it in d}
print('报警条目数:', len(by_id))
print('')
for i in (0x63, 0x74, 0x79, 0x7E, 0x82, 0x86, 0xEE31 & 0xFF, 130, 118, 126, 121):
    it = by_id.get(i)
    if not it:
        print('  id %-5d (0x%02X)  ---  表中无此项' % (i, i))
        continue
    zh = it.get('zh_CN', {})
    en = it.get('en', {})
    print('  id %-5d (0x%02X)  level=%s' % (i, i, it.get('level')))
    print('     中文描述: %s' % zh.get('description', ''))
    if zh.get('cause'):
        print('     原因    : %s' % zh.get('cause', '')[:160])
    if zh.get('solution'):
        print('     解决    : %s' % zh.get('solution', '')[:200])
    print('     EN      : %s' % en.get('description', ''))
    print('')
