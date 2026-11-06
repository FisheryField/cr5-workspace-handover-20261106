# -*- coding: utf-8 -*-
"""轨迹13 场景匹配平移（用户指令 2026-10-20）：
- P1、P21（首末出入点，y=0）不动；
- P2–P20 全部 y−82（与圆柱/挡板后移 82 同步，尖端-工件相对关系保持）。
- 先备份，LF/indent=2 与原文件一致。不跑预检（用户明示暂不考虑成败）。
"""
import sys, io, json, shutil, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
BAK = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13_preYshift82_20261020.json.bak'

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print('备份:', BAK)
else:
    print('备份已存在（不覆盖）:', BAK)

records = json.load(open(SRC, encoding='utf-8'))
assert len(records) == 21, len(records)
assert abs(float(records[0]['values'][1])) < 1e-9, 'P1 应在 y=0'
assert abs(float(records[20]['values'][1])) < 1e-9, 'P21 应在 y=0'

changed = 0
for i in range(1, 20):          # P2..P20
    v = [float(t) for t in records[i]['values']]
    v[1] -= 82.0
    records[i]['values'] = v
    changed += 1
    print('P%-2d y → %.1f   (x=%.1f z=%.1f)' % (i + 1, v[1], v[0], v[2]))

assert changed == 19
with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(records, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('已写入：%d 点平移，P1/P21 未动' % changed)
print('DONE')
