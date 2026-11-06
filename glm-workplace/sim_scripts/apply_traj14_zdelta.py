# -*- coding: utf-8 -*-
"""轻量应用 (Z, Δ)：写轨迹14（P2–P20: y+=Δ, z=Z）+ 场景（圆柱 pose.y=−840+Δ ⇒ 面表=−700+Δ；挡板保持相对偏移）。
用法：python apply_traj14_zdelta.py Z DELTA
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

Z = float(sys.argv[1]); DELTA = float(sys.argv[2])
SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
DST = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'

recs = json.load(open(SRC, encoding='utf-8'))
out = []
for i, rec in enumerate(recs, 1):
    v = [float(t) for t in rec['values']]
    if i not in (1, 21):
        v[1] += DELTA
        v[2] = Z
    e = dict(rec); e['values'] = v
    out.append(e)
with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False); f.write('\n')

RDK = Robolink()
cyl = RDK.Item('磨砂圆柱_R150_H50')
baf = RDK.Item('挡板_半封闭3面')
p_c = Pose_2_Fanuc(cyl.Pose())
p_b = Pose_2_Fanuc(baf.Pose())
rel = p_b[1] - p_c[1]                      # 挡板-圆柱 pose.y 偏移保持
new_cyl_y = -840.0 + DELTA                 # 面表 = pose.y+140 = −700+Δ
cyl.setPose(Fanuc_2_Pose([p_c[0], new_cyl_y, p_c[2], p_c[3], p_c[4], p_c[5]]))
baf.setPose(Fanuc_2_Pose([p_b[0], new_cyl_y + rel, p_b[2], p_b[3], p_b[4], p_b[5]]))
print('Z=%g Δ=%+g  圆柱 pose.y=%.0f（面表 %.0f） 挡板 pose.y=%.0f  轨迹14 已写'
      % (Z, DELTA, new_cyl_y, new_cyl_y + 140, new_cyl_y + rel))
