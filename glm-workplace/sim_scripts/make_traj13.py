# -*- coding: utf-8 -*-
"""由轨迹11 生成轨迹13：非转运点(y≠0) y+203、全部点 z+170；其余字段原样保留。"""
import json

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹11.json'
DST = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'

with open(SRC, 'r', encoding='utf-8') as f:
    src = json.load(f)

out = []
for i, p in enumerate(src):
    v = [float(x) for x in p['values']]
    if abs(v[1]) > 1e-9:        # 工作点随图案平移
        v[1] = v[1] + 203.0
    v[2] = v[2] + 170.0         # 全部抬到新场景高度
    entry = dict(p)             # 保留 type/singular/spin360/j6_delta 等全部字段
    entry['values'] = v
    out.append(entry)

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write('\n')

print('已写入 %s（%d 点）' % (DST, len(out)))
for i, p in enumerate(out):
    flags = []
    if p.get('singular'): flags.append('singular')
    if p.get('spin360'): flags.append('spin360')
    if p.get('j6_delta'): flags.append('j6_delta=%s' % p['j6_delta'])
    print('%2d  %-42s %s' % (i, p['values'], ' '.join(flags)))
