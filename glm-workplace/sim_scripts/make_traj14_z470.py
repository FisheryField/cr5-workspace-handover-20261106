# -*- coding: utf-8 -*-
"""连续轨迹14 v2（用户约束 2026-10-20）：全部点 z=470 固定 + 仅 P8–P12 的 y −686→−600。
依据：scan_z470_y_edges.py 实测（tool=182）——rx180 簇 x0/x100 边界 −630/−620，−600 留 20–30mm；
其余姿态族边界 −715~−860，原始 y 全部可达。其余字段（singular/spin360/j6_delta/type）原样继承轨迹13。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
DST = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'

recs = json.load(open(SRC, encoding='utf-8'))
assert len(recs) == 21

out = []
for i, rec in enumerate(recs, 1):
    v = [float(t) for t in rec['values']]
    v[2] = 470.0                      # 高度锁 470
    if 8 <= i <= 12:
        v[1] = -600.0                 # rx180 簇退到可达区（边界-630/-620 + 余量）
    entry = dict(rec)
    entry['values'] = v
    out.append(entry)
    print('P%-2d (%7.1f,%7.1f,%5.1f, %5.1f,%4.1f,%5.1f)  %s%s' % (
        i, v[0], v[1], v[2], v[3], v[4], v[5],
        ('spin360 ' if rec.get('spin360') else ''),
        ('j6d=%s ' % rec.get('j6_delta') if rec.get('j6_delta') else '')))

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('已写入:', DST)
