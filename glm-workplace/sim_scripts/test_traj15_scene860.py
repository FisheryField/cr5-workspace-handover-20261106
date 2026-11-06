# -*- coding: utf-8 -*-
"""矩阵补测：场景临时 +26 还原到 −860，测 traj15@126+场景−860；测完再退回 −886。"""
import sys, io, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

RDK = robolink.Robolink()
cyl = RDK.Item('磨砂圆柱_R150_H50')
baf = RDK.Item('挡板_半封闭3face') if RDK.Item('挡板_半封闭3face').Valid() else RDK.Item('挡板_半封闭3面')
c0 = Pose_2_Fanuc(cyl.Pose())
b0 = Pose_2_Fanuc(baf.Pose())
print('当前 圆柱 y=%.1f 挡板 y=%.1f' % (c0[1], b0[1]))

sys.path.insert(0, r'D:\software\RoboDK\Python-Embedded\Lib\site-packages')
PY = r'D:\software\RoboDK\Python-Embedded\python.exe'
try:
    cyl.setPose(Fanuc_2_Pose([c0[0], c0[1] + 26.0, c0[2], c0[3], c0[4], c0[5]]))
    baf.setPose(Fanuc_2_Pose([b0[0], b0[1] + 26.0, b0[2], b0[3], b0[4], b0[5]]))
    p = Pose_2_Fanuc(cyl.Pose())
    print('临时还原到 圆柱 y=%.1f' % p[1])
    r = subprocess.run([PY, r'D:\mydata\glm-workplace\sim_scripts\verify_traj15_plan.py'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900)
    tail = (r.stdout or '')[-2500:]
    print('=== traj15 @126 + 场景-860 ===')
    print(tail)
finally:
    cyl.setPose(Fanuc_2_Pose([c0[0], c0[1], c0[2], c0[3], c0[4], c0[5]]))
    baf.setPose(Fanuc_2_Pose([b0[0], b0[1], b0[2], b0[3], b0[4], b0[5]]))
    p = Pose_2_Fanuc(cyl.Pose())
    print('场景已退回 圆柱 y=%.1f' % p[1])
print('DONE')
