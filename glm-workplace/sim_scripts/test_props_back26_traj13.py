# -*- coding: utf-8 -*-
"""测试：圆柱+挡板 y-26 后，tool=126 下轨迹13(z460统一版) 能否通过。
结束后场景自动 +26 还原（工具由外部还原182）。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

DY = -26.0
RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
print('PoseTool =', robot.PoseTool().Pos())

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)

cyl = RDK.Item('磨砂圆柱_R150_H50')
baf = RDK.Item('挡板_半封闭3面')
assert cyl.Valid() and baf.Valid(), '场景物件缺失'
c0 = Pose_2_Fanuc(cyl.Pose())
b0 = Pose_2_Fanuc(baf.Pose())
print('圆柱 BEFORE y = %.1f ; 挡板 BEFORE y = %.1f' % (c0[1], b0[1]))

try:
    cyl.setPose(Fanuc_2_Pose([c0[0], c0[1] + DY, c0[2], c0[3], c0[4], c0[5]]))
    baf.setPose(Fanuc_2_Pose([b0[0], b0[1] + DY, b0[2], b0[3], b0[4], b0[5]]))
    print('已移动 %.0fmm → 圆柱 y=%.1f 挡板 y=%.1f' % (DY, c0[1] + DY, b0[1] + DY))

    TMP = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13_t126_z460.json'
    records = ns['_retreat_orientation_records'](json.load(open(TMP, encoding='utf-8')))
    robot.setJoints([0.0] * 6)
    RDK.setRunMode(robolink.RUNMODE_SIMULATE)
    def log(m):
        print('  |', m)
    try:
        plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
        print('\n=== 预检通过：%d 段 ===' % len(plan))
        print('RESULT: PASS')
    except ValueError as exc:
        print('\n=== 预检失败 ===')
        print(' ', exc)
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
finally:
    cyl.setPose(Fanuc_2_Pose([c0[0], c0[1], c0[2], c0[3], c0[4], c0[5]]))
    baf.setPose(Fanuc_2_Pose([b0[0], b0[1], b0[2], b0[3], b0[4], b0[5]]))
    print('场景已还原（圆柱 y=%.1f 挡板 y=%.1f）' % (c0[1], b0[1]))
print('DONE')
