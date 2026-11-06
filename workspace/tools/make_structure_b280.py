#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 structure.json 里 J2 的 limits 从 [-235,235] 再放宽到 [-280,280]。
   输入 = 从控制器下载的当前线上文件；输出 = structure_b280.json。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC = r'D:\mydata\workspace\data\structure_b235.json'
DST = r'D:\mydata\workspace\data\structure_b280.json'
OLD = [-235, 235]
NEW = [-280, 280]

raw = io.open(SRC, encoding='utf-8').read()
print('原始字节数 =', len(raw.encode('utf-8')))
before = json.loads(raw)
print('改前 limits =', before['structure']['limits'])
assert before['structure']['limits'][1] == OLD, 'J2 现值不是 [-235,235]'

lines = raw.split('\n')
li = next(i for i, l in enumerate(lines) if '"limits"' in l)
opens = [i for i in range(li, len(lines)) if lines[i].strip() == '['][:6]
print('"limits" 行 = %d, 6 个 [ 行 = %s' % (li, opens))
assert len(opens) == 6
j2 = opens[1]
print('J2 两行原文: %r , %r' % (lines[j2 + 1], lines[j2 + 2]))
assert '-235' in lines[j2 + 1] and '235' in lines[j2 + 2]

lines[j2 + 1] = lines[j2 + 1].replace('-235', '%d' % NEW[0])
lines[j2 + 2] = lines[j2 + 2].replace('235', '%d' % NEW[1])
raw2 = '\n'.join(lines)

after = json.loads(raw2)
print('')
print('改后 limits =', after['structure']['limits'])
assert after['structure']['limits'][1] == NEW
assert after['structure']['limits'][0] == before['structure']['limits'][0]
assert after['structure']['limits'][2:] == before['structure']['limits'][2:]

b2 = json.loads(raw)
a2 = json.loads(raw2)
b2['structure']['limits'][1] = NEW
assert b2 == a2, '除 J2 外还有字段被改动！'
print('✓ 只改了 J2 的 limits，其余逐项一致')

io.open(DST, 'w', encoding='utf-8', newline='').write(raw2)
print('已写出 =', DST, ' 字节 =', len(raw2.encode('utf-8')))
