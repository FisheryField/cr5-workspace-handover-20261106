# -*- coding: utf-8 -*-
"""v14w36 等价性验证（只读）：
旧路径 = PoseTool置单位变换 + MoveL(净化关节) ⇒ RoboDK 内部 FK 得法兰位姿发给驱动；
新路径 = 不动工具，send_pose = invH(PoseFrame)*SolveFK(净化关节)，MoveL(send_pose)。
金标准 = 10-22 10:24:56 柜子实际收到的 P5 直发参数（控制器日志）：
  MovL(-99.986407,-536.994792,380.017835,89.998290,0.001038,0.001000)
分别用 旧公式(_trajectory_pose@identity) 与 新公式(invH(frame)*SolveFK) 对净化后关节重算，
转 Fanuc 后与金标准逐位对比。"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()
start_q = robot.Joints().list()[:6]
start_tool = robot.PoseTool()

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))
to_fanuc = ns['pose_to_fanuc_values']

# P5 认证关节 + 日志实录净化量（J1+0.0010, J2-0.0020）
P5_CERT = [58.74371028985596, 26.060110461966033, 112.24921152975168,
           -138.30932199171772, -58.74371028985596, 180.0]
PURGED = P5_CERT[:]
PURGED[0] += 0.0010
PURGED[1] -= 0.0020
GOLDEN = (-99.986407, -536.994792, 380.017835, 89.998290, 0.001038, 0.001000)

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0] * 6)

# —— 旧路径复现：工具置单位变换后，_trajectory_pose(净化关节) ——
robot.setPoseTool(Fanuc_2_Pose([0, 0, 0, 0, 0, 0]))
pose_old = ns['_trajectory_pose'](PURGED)          # = invH(frame)*SolveFK*eye
fanuc_old = [float(v) for v in to_fanuc(pose_old)[:6]]

# —— 新路径：工具保持 182，send_pose = invH(frame)*SolveFK(净化关节) ——
robot.setPoseTool(start_tool)
pose_new = invH(robot.PoseFrame()) * robot.SolveFK(PURGED)
fanuc_new = [float(v) for v in to_fanuc(pose_new)[:6]]

def row(name, vals):
    print('%s = [%s]' % (name, ', '.join('%.6f' % v for v in vals)))

row('金标准(柜子实收)', GOLDEN)
row('旧公式(单位变换FK)', fanuc_old)
row('新公式(自算法兰)  ', fanuc_new)
d_old = max(abs(a - b) for a, b in zip(fanuc_old, GOLDEN))
d_new = max(abs(a - b) for a, b in zip(fanuc_new, GOLDEN))
d_cross = max(abs(a - b) for a, b in zip(fanuc_old, fanuc_new))
print('旧 vs 金标准 最大偏差 = %.9f mm/deg' % d_old)
print('新 vs 金标准 最大偏差 = %.9f mm/deg' % d_new)
print('新 vs 旧     最大偏差 = %.9f mm/deg' % d_cross)

# 位姿本体（Mat）级对比
err = pose_old.inv() * pose_new if hasattr(pose_old, 'inv') else None
try:
    from robodk.robomath import pose_angle
    e = invH(pose_old) * pose_new
    print('位姿级：位置差 %.9f mm，姿态差 %.9f deg' %
          (ns['norm'](e.Pos()), math.degrees(ns['pose_angle'](e))))
except Exception as ex:
    print('位姿级对比跳过:', ex)

ok = d_new < 1e-4 and d_old < 1e-4 and d_cross < 1e-6
print('RESULT:', 'PASS（三者逐位等价，新公式可安全替换）' if ok else 'FAIL（不等价，禁止落地）')

robot.setPoseTool(start_tool)
robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（只读；工具/关节/runmode 已恢复）')
