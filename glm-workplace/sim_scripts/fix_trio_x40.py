# -*- coding: utf-8 -*-
"""轨迹15 修订：三旋转点从 (20,-707) 挪到 (40,-694)（姿态角不变），
并在其前面插入过渡点 (40,-694,90,0,90)（=J6+0）。之后跑整段预检。"""
import sys, io, json, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹15.json'
records = json.load(open(PATH, encoding='utf-8'))
print('原点数 =', len(records))

# 校验三旋转点位置（x=20,y=-707）
for k in (14, 15, 16):
    v = records[k]['values']
    assert abs(v[0] - 20.0) < 1e-6 and abs(v[1] + 707.0) < 1e-6, '第%d点不是预期三旋转点: %s' % (k + 1, v)

ts = time.strftime('%Y%m%d-%H%M')
bak = PATH.replace('.json', '_pre_move40_%s.json.bak' % ts)
shutil.copy2(PATH, bak)
print('备份 =', bak)

# 1) 三旋转点改到 (40,-694)
for k in (14, 15, 16):
    records[k]['values'][0] = 40.0
    records[k]['values'][1] = -694.0

# 2) 前插过渡点 = J6+0 @ (40,-694,90,0,90)
trans = {'type': 'TCP', 'values': [40.0, -694.0, 380.0, 90.0, 0.0, 90.0],
         'singular': False, 'j6_delta': 0}
records = records[:14] + [trans] + records[14:]

open(PATH, 'w', encoding='utf-8').write(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
chk = json.load(open(PATH, encoding='utf-8'))
print('插入后点数 =', len(chk))
print('P15(过渡) =', chk[14]['values'])
for k in (15, 16, 17):
    print('P%d = %s' % (k + 1, chk[k]['values']))
print('DONE')
