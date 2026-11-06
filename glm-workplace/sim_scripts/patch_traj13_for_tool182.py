# -*- coding: utf-8 -*-
"""轨迹13 适配 tool=182：6 个不可达点 z−82（rx=180 朝下点 ⇒ 法兰恰回 tool=100 旧位，可证可达）。
P8/P9/P10/P11/P12: z 470→388；P13: z 570→488。其余点一律不动。
先备份 .bak，断言命中数=5+1，LF 换行、indent=2 与原文件一致。
"""
import sys, io, json, shutil, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
BAK = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13_pre182fix_20261020.json.bak'

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print('备份:', BAK)
else:
    print('备份已存在（不覆盖）:', BAK)

records = json.load(open(SRC, encoding='utf-8'))
print('点数:', len(records))

changed = []
for i, rec in enumerate(records, 1):
    v = rec.get('values')
    if not v or rec.get('type') != 'TCP':
        continue
    x, y, z, rx, ry, rz = [float(t) for t in v]
    new_z = None
    if abs(y - (-686.0)) < 1e-9 and abs(z - 470.0) < 1e-9 and abs(abs(rx) - 180.0) < 1e-9:
        new_z = 388.0
    elif abs(y - (-486.0)) < 1e-9 and abs(z - 570.0) < 1e-9 and abs(abs(rx) - 180.0) < 1e-9:
        new_z = 488.0
    if new_z is not None:
        changed.append((i, z, new_z))
        rec['values'] = [x, y, new_z, rx, ry, rz]

print('命中改动:', len(changed), '条')
for i, old, new in changed:
    print('  P%d: z %.1f → %.1f' % (i, old, new))

n470 = sum(1 for c in changed if c[1] == 470.0)
n570 = sum(1 for c in changed if c[1] == 570.0)
if not (n470 == 5 and n570 == 1 and len(changed) == 6):
    print('!!! 断言失败（期望 470→388×5 + 570→488×1），中止，不写盘')
    sys.exit(1)

with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(records, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('已写入（LF、indent=2）:', SRC)
print('DONE')
