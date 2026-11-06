# -*- coding: utf-8 -*-
"""轨迹16 微调：P23/P25 y −674 → −665（压缩把手下的净空边界内）。备份原文件。"""
import sys, io, json, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹16.json'
records = json.load(open(PATH, encoding='utf-8'))
print('点数 =', len(records))
for k in (22, 24):   # P23, P25
    v = records[k]['values']
    print('P%d 改前 = %s' % (k + 1, v))
    assert abs(float(v[1]) + 674.0) < 1e-6, 'P%d y 不是 -674' % (k + 1)
    v[1] = -665.0

ts = time.strftime('%Y%m%d-%H%M')
bak = PATH.replace('.json', '_pre_tilt665_%s.json.bak' % ts)
shutil.copy2(PATH, bak)
print('备份 =', bak)
open(PATH, 'w', encoding='utf-8').write(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
chk = json.load(open(PATH, encoding='utf-8'))
for k in (22, 24):
    print('P%d 改后 = %s' % (k + 1, chk[k]['values']))
print('DONE')
