# -*- coding: utf-8 -*-
"""由轨迹7 生成轨迹12：工作点(1..8) y+76、全部点 z+170；singular/j6_delta 原样保留。
（Δ=+76：与轨迹13 同版落位 线A=-699/圆柱-840/挡板76；自干涉修复后的新基准。）"""
import json

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json'
DST = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹12.json'

with open(SRC, 'r', encoding='utf-8') as f:
    src = json.load(f)

out = []
for i, p in enumerate(src):
    v = [float(x) for x in p['values']]
    if 1 <= i <= 8:
        v[1] = v[1] + 76.0
    v[2] = v[2] + 170.0
    out.append({
        'type': p['type'],
        'values': v,
        'singular': p['singular'],
        'j6_delta': p['j6_delta'],
    })

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write('\n')

print('已写入 %s（%d 点）' % (DST, len(out)))
for i, p in enumerate(out):
    print('%2d  %s' % (i, p['values']))
