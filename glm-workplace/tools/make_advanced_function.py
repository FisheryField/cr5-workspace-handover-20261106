#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 AdvancedFunction.json 的 SteadyErrorThreshold 改成 1.0×6，其余一字不动。"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC = r'D:\mydata\workspace\data\AdvancedFunction_orig.json'
DST = r'D:\mydata\workspace\data\AdvancedFunction_new.json'

raw = io.open(SRC, encoding='utf-8').read()
print('原始字节数 =', len(raw.encode('utf-8')))

# 先确认 JSON 合法、并记录改动前的值
before = json.loads(raw)
print('SteadyErrorThreshold 改前 =', before['SteadyErrorThreshold'])
print('FollowError 改前          =', before['FollowError'])

# 只替换 SteadyErrorThreshold 那个数组块（保留原有缩进风格：4 空格 + 8 空格）
pat = re.compile(r'("SteadyErrorThreshold"\s*:\s*\[)(.*?)(\])', re.S)
new_block = '\n' + ',\n'.join(['        1.0'] * 6) + '\n    '
raw2, n = pat.subn(lambda m: m.group(1) + new_block + m.group(3), raw, count=1)
print('替换次数 =', n)
assert n == 1, '未替换或替换多次'

# 校验
after = json.loads(raw2)
print('改后 SteadyErrorThreshold =', after['SteadyErrorThreshold'])
assert after['SteadyErrorThreshold'] == [1.0] * 6
# 其余字段必须完全一致
after['SteadyErrorThreshold'] = before['SteadyErrorThreshold']
assert after == before, '除 SteadyErrorThreshold 外还有字段被改动！'
print('✓ 其余字段逐项一致（只改了 SteadyErrorThreshold）')

io.open(DST, 'w', encoding='utf-8', newline='').write(raw2)
print('已写出 =', DST, ' 字节数 =', len(raw2.encode('utf-8')))
print('')
print('--- 改后文件全文 ---')
print(raw2)
