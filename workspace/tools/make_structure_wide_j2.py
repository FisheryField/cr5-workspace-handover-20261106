#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 structure.json 里 "limits" 数组的【第 2 个元素（J2）】从 [-178,178] 改成 [-235,235]。
   其余一字不动，并做严格校验。"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC = r'D:\mydata\workspace\data\structure_orig.json'
DST = r'D:\mydata\workspace\data\structure_new.json'

raw = io.open(SRC, encoding='utf-8').read()
print('原始字节数 =', len(raw.encode('utf-8')))

before = json.loads(raw)
old_limits = before['structure']['limits']          # ★ 实际路径是 /structure/limits
print('改前 limits  =', old_limits)
assert isinstance(old_limits, list) and len(old_limits) == 6, 'limits 结构不符预期'

J2_OLD = old_limits[1]
J2_NEW = [-235, 235]
print('J2 改前 =', J2_OLD, ' ->  改后 =', J2_NEW)
assert J2_OLD == [-178, 178], 'J2 现值不是 [-178,178]，先别改'

# 用行级定位（格式规整：每个 [ 独占一行，值各占一行），最可靠
lines = raw.split('\n')
li = next(i for i, l in enumerate(lines) if '"limits"' in l)
opens = [i for i in range(li, len(lines)) if lines[i].strip() == '['][:6]
print('"limits" 行号 = %d，6 个 [ 的行号 = %s' % (li, opens))
assert len(opens) == 6, '块内 [ 不是 6 个'

j2 = opens[1]                      # 第 2 个 = J2
print('J2 的两行原文: %r , %r' % (lines[j2 + 1], lines[j2 + 2]))
assert '-178' in lines[j2 + 1] and '178' in lines[j2 + 2], 'J2 数值行不符预期'

lines[j2 + 1] = lines[j2 + 1].replace('-178', '%d' % J2_NEW[0])
lines[j2 + 2] = lines[j2 + 2].replace('178', '%d' % J2_NEW[1])
print('J2 的两行改后: %r , %r' % (lines[j2 + 1], lines[j2 + 2]))
raw2 = '\n'.join(lines)

after = json.loads(raw2)
print('')
print('改后 limits  =', after['structure']['limits'])
assert after['structure']['limits'][1] == J2_NEW, 'J2 未改成功'
assert after['structure']['limits'][0] == old_limits[0] and \
       after['structure']['limits'][2:] == old_limits[2:], '改动了其它轴！'

# 除 J2 那一项外，其它字段必须完全一致
b2 = json.loads(raw)
a2 = json.loads(raw2)
b2['structure']['limits'][1] = J2_NEW
assert b2 == a2, '除 J2 的 limits 外还有字段被改动！'
print('✓ 只改了 J2 的 limits，其余字段逐项一致')

io.open(DST, 'w', encoding='utf-8', newline='').write(raw2)
print('已写出 =', DST, ' 字节数 =', len(raw2.encode('utf-8')))
print('')
print('--- 改后的 limits 块 ---')
m2 = re.search(r'"limits"\s*:\s*\[.*?\n\s*\]', raw2, re.S)
print(m2.group(0) if m2 else '(未找到)')
