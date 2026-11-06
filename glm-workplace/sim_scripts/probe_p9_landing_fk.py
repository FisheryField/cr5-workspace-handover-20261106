# -*- coding: utf-8 -*-
"""P9 迟到落点几何定性（只读：只调 SolveFK/PoseTool，不 setJoints、不改 runmode、不发指令）。

背景：P9 法兰补偿直发超时后，臂反复停在 [-63.41,-13.45,-66.65,-69.89,-63.41,0]
（日志 6 次），而不是计划目标 [-74.106,-22.194,-88.535,-69.270,-74.106,0]。
本探针判定迟到落点的法兰位姿等于哪个候选位姿：
  T1: FK(P9)                ⇒ 送达的就是法兰目标（直发几何正确，另有他因）
  T2: FK(P9)*tool           ⇒ 送达位姿 = TCP(P9)（= 超时 finally 恢复工具后才换算/送达）
  T3: FK(落点)*tool == FK(P9) ⇒ 控制器按"带工具"执行（落点的 TCP = P9 法兰）
  T4: FK(P9)*inv(tool)
另核对 P5/P9 镜像关系：FK(P9) 与 FK(P4) 应只差绕 z 轴 180°（J6 差 -180），法兰中心同位。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH, norm, pose_angle

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

J_P8 = [-63.41392174214573, -23.452600702069333, -86.65404121903774,
        -69.89335807889292, -63.41392174214573, 0.0]
J_P9 = [-74.10620847168758, -22.194417181878357, -88.53508496756278,
        -69.27049785055885, -74.10620847168758, 0.0]
J_P4 = [-74.10620847168758, -22.19441718187838, -88.53508496756277,
        -69.27049785055884, -74.10620847168758, -180.0]
J_P5 = [-63.41392174214573, -23.452600702069333, -86.65404121903774,
        -69.89335807889292, -63.41392174214573, -180.0]
J_LAND = [-63.41, -13.45, -66.65, -69.89, -63.41, 0.0]  # 迟到落点（日志 6 次同值）

tool = robot.PoseTool()
print('station PoseTool: pos=%s rot(deg)=%s' % (
    ['%.3f' % v for v in tool.Pos()],
    ['%.3f' % v for v in [pose_angle(tool) * 57.29578 * 0]]))  # placeholder,详细见下
print('tool 位置模长 = %.3f mm' % norm(tool.Pos()))

def report(name, a, b):
    d = a * invH(b)
    print('%-38s 位置差=%8.3f mm  姿态差=%7.3f°' % (name, norm(d.Pos()), pose_angle(d) * 57.29578))

F8, F9, F4, F5, FL = (robot.SolveFK(j) for j in (J_P8, J_P9, J_P4, J_P5, J_LAND))
TCP9 = F9 * tool
TCP5 = F5 * tool

print('--- 迟到落点判定 ---')
report('T1 落点法兰 vs FK(P9)', FL, F9)
report('T2 落点法兰 vs FK(P9)*tool', FL, TCP9)
report('T3 落点法兰*tool vs FK(P9)', FL * tool, F9)
report('T4 落点法兰 vs FK(P9)*inv(tool)', FL, F9 * invH(tool))
print('--- 参照：P5 成功场（应为法兰级吻合） ---')
report('P5/P9 镜像: FK(P9) vs FK(P4)', F9, F4)          # 期望：位置0，姿态180°
report('P5/P9 镜像: FK(P8) vs FK(P5)', F8, F5)
report('落点 vs P8(起点)', FL, F8)                        # 实际动了多少
print('--- 段几何 ---')
print('法兰直线 |FK(P8)-FK(P9)| = %.3f mm' % norm((F8 * invH(F9)).Pos()))
print('法兰直线 |FK(P8)-TCP(P9)| = %.3f mm（v14l 型错误目标）' % norm((F8 * invH(TCP9)).Pos()))
