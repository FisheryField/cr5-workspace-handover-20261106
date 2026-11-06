#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1) 列出 alarm_servo.json 里 0x71xx / 0x84xx / 0x86xx 整族；
   2) 在厂商参数表 hparam_map.json / param.csv 里搜"位置/给定/范围/超限/偏差"相关参数。"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = json.loads(io.open(r'D:\mydata\workspace\data\alarm_servo.json',
                       encoding='utf-8', errors='replace').read())
by_id = {int(it['id']): it for it in d if isinstance(it, dict) and 'id' in it}

print('=== A) 位置/速度/过载 保护族 ===')
for code in sorted(by_id):
    if (code >> 8) in (0x71, 0x84, 0x86, 0x85, 0xFF):
        zh = by_id[code].get('zh_CN', {})
        en = by_id[code].get('en', {})
        print('  0x%04X (%-5d) %-22s | %s' % (code, code,
                                              zh.get('description', '')[:20],
                                              en.get('description', '')[:58]))

print('')
print('=== B) 厂商参数表里与"位置/给定/范围/偏差"有关的条目 ===')
P = r'D:\mydata\workspace\data\servo_fw_samples\hparam_map.json'
try:
    hm = json.loads(io.open(P, encoding='utf-8', errors='replace').read())
except Exception as e:  # noqa: BLE001
    print('  读 hparam_map.json 失败: %s' % e)
    hm = None
KW = ('位置', '给定', '范围', '超限', '偏差', 'pos', 'Pos', 'range', 'Range', 'limit', 'Limit',
      'error', 'Error', 'over', 'Over', 'deviation')
if isinstance(hm, dict):
    print('  hparam_map.json 条目数 =', len(hm))
    shown = 0
    for k, v in hm.items():
        s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        if any(w in s for w in KW) or any(w in str(k) for w in KW):
            print('   %-14s -> %s' % (k, s[:150]))
            shown += 1
            if shown >= 60:
                print('   ... (截断)')
                break
elif isinstance(hm, list):
    print('  hparam_map.json 是列表，长度 =', len(hm))
    print('  样例:', json.dumps(hm[0], ensure_ascii=False)[:250] if hm else '')
    shown = 0
    for it in hm:
        s = json.dumps(it, ensure_ascii=False)
        if any(w in s for w in KW):
            print('   ', s[:170])
            shown += 1
            if shown >= 60:
                print('   ... (截断)')
                break
