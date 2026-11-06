# -*- coding: utf-8 -*-
"""在旋转组回基座角（(40,-694,90,0,90)）之后，追加终终点 (−20,−707,380,90,0,90)。"""
import sys, io, json, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹15.json'
records = json.load(open(PATH, encoding='utf-8'))
print('原点数 =', len(records))

# 找旋转组后的基座角点 (40,-694,90,0,90) —— 应为 idx18
idx = None
for k in range(14, len(records)):
    v = records[k]['values']
    if (abs(v[0] - 40.0) < 1e-6 and abs(v[1] + 694.0) < 1e-6
            and abs(v[3] - 90.0) < 1e-6 and abs(v[4]) < 1e-6 and abs(v[5] - 90.0) < 1e-6):
        idx = k
print('基座角回位点 = P%d (%s)' % (idx + 1, records[idx]['values']))
print('其后一点 = P%d (%s)' % (idx + 2, records[idx + 1]['values']))

ts = time.strftime('%Y%m%d-%H%M')
bak = PATH.replace('.json', '_pre_final20_%s.json.bak' % ts)
shutil.copy2(PATH, bak)
print('备份 =', bak)

final_pt = {'type': 'TCP', 'values': [-20.0, -707.0, 380.0, 90.0, 0.0, 90.0],
            'singular': False, 'j6_delta': 0}
records = records[:idx + 1] + [final_pt] + records[idx + 1:]
open(PATH, 'w', encoding='utf-8').write(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
chk = json.load(open(PATH, encoding='utf-8'))
print('插入后点数 =', len(chk))
print('P%d (新终终点) = %s' % (idx + 2, chk[idx + 1]['values']))
print('DONE')
