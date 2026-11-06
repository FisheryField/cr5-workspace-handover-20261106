#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查厂商伺服报警表 alarm_servo.json 里的 0x8612 / 0x8481 / 0x7180 等码。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\alarm_servo.json'
d = json.loads(io.open(P, encoding='utf-8', errors='replace').read())
print('顶层类型 =', type(d).__name__, ' 条目数 =', len(d) if hasattr(d, '__len__') else '?')

items = d if isinstance(d, list) else d.get('body', d)
if isinstance(items, dict):
    items = [{'id': k, **v} if isinstance(v, dict) else {'id': k, 'val': v} for k, v in items.items()]

by_id = {}
for it in items:
    if not isinstance(it, dict):
        continue
    for k in ('id', 'alarmId', 'code', 'errorId', 'value'):
        if k in it:
            try:
                by_id[int(str(it[k]), 0)] = it
            except (ValueError, TypeError):
                pass
            break

print('可索引条目数 =', len(by_id))
print('')
print('=== 样例（前 2 条）===')
for it in items[:2]:
    print(' ', json.dumps(it, ensure_ascii=False)[:300])
print('')
for code in (0x8612, 0x8481, 0x7180, 34322, 33921, 29056, 0x8611, 0x8613):
    it = by_id.get(code)
    print('--- 0x%04X (%d)' % (code, code))
    if it:
        print('   ', json.dumps(it, ensure_ascii=False)[:600])
    else:
        print('    (表中无此项)')
