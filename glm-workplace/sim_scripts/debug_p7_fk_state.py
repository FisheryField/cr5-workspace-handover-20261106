# -*- coding: utf-8 -*-
"""只读调试：P6 关节 FK 残差 / 站内 PoseTool、PoseFrame 状态 / seg 计算复测。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH, norm

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()
print('model joints now =', [round(v, 2) for v in robot.Joints().list()[:6]])

pt = robot.PoseTool()
pf = robot.PoseFrame()
print('PoseTool.Pos =', pt.Pos())
print('PoseFrame.Pos =', pf.Pos())
print('PoseTool rows =', pt.rows)

P6_Q = [-67.43858771971193, -17.80254851667152, -126.39845591028943,
        144.20100442696094, 67.43858771971193, 180.0]
pose6 = Fanuc_2_Pose([0.0, -650.0, 380.0, 90.0, 0.0, 0.0])
pose7 = Fanuc_2_Pose([0.0, -650.0, 380.0, 180.0, 0.0, 0.0])

fk = robot.SolveFK(P6_Q)
print('SolveFK(P6_Q).Pos =', fk.Pos())
print('pose6.Pos =', pose6.Pos(), ' pose7.Pos =', pose7.Pos())
print('d(SolveFK, pose6) = %.4f' % norm((invH(pose6) * fk).Pos()))
print('d(SolveFK, pose7) = %.4f' % norm((invH(pose7) * fk).Pos()))

traj = invH(pf) * fk * pt
print('traj(P6_Q).Pos =', traj.Pos())
print('seg traj-vs-pose7 = %.4f' % norm((traj * invH(pose7)).Pos()))
print('seg traj-vs-pose6 = %.4f' % norm((traj * invH(pose6)).Pos()))

# 自洽性：当前状态 IK→FK 往返
flange7 = pf * pose7 * invH(pt)
sols = robot.SolveIK_All(flange7)
try:
    lst = sols.tolist()
except Exception as e:
    lst = []
print('SolveIK_All(pose7 flange) count =', len(lst))
if lst:
    q0 = lst[0][:6] if isinstance(lst[0], list) else lst[0]
    fk0 = robot.SolveFK(q0)
    print('FK(IK(pose7)) d vs pose7 = %.6f' % norm((invH(pose7) * fk0).Pos()))
print('DONE')
