#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查 0x45(69) 及相关报警；并列出可能与"关节不动/限位"有关的条目。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = json.loads(io.open(r'D:\mydata\workspace\data\alarm_controller.json', encoding='utf-8').read())
by_id = {int(it['id']): it for it in d}


def show(i):
    it = by_id.get(i)
    if not it:
        print('  id %-5d (0x%02X)  --- 表中无' % (i, i))
        return
    zh, en = it.get('zh_CN', {}), it.get('en', {})
    print('  id %-5d (0x%02X) level=%s' % (i, i, it.get('level')))
    print('     中文: %s' % zh.get('description', ''))
    if zh.get('cause'):
        print('     原因: %s' % zh.get('cause', '')[:170])
    if zh.get('solution'):
        print('     解决: %s' % zh.get('solution', '')[:220])
    print('     EN  : %s' % en.get('description', ''))


print('=== 0x45 (69) ===')
show(0x45)
print('')
print('=== 与"关节/限位/超程/偏差"有关的条目 ===')
kw = ('限位', '超程', '超出', '偏差', '关节', '编码器', '过载', '堵转', '失速', '抱闸', '刹车')
for i in sorted(by_id):
    it = by_id[i]
    t = it.get('zh_CN', {}).get('description', '') or ''
    if any(k in t for k in kw):
        print('  %-5d (0x%02X) lv=%s  %s' % (i, i, it.get('level'), t))
