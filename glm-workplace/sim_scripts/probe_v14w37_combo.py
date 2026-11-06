# -*- coding: utf-8 -*-
"""v14w37 组合方案预验证（只读仿真）：
位姿传递 + 单位变换（flange_space）——①P8 位姿在单位变换下 MoveL 不再抛
TargetReachError；②认证直线端点/中点在单位变换工具下无碰撞（动画窗口安全）。"""
import sys, io, json
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
records = ns['_retreat_orientation_records'](
    json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹14.json', encoding='utf-8')))

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0] * 6)
plan = ns['_plan_continuous_trajectory'](records, 500.0, lambda m: None)
P7Q = list(plan[6]['joints'])
P8Q = list(plan[7]['joints'])
P5Q = list(plan[4]['joints'])
purged8, _ = ns['_movl_digit_safe_joints'](P8Q)
purged5, _ = ns['_movl_digit_safe_joints'](P5Q)

robot.setPoseTool(Fanuc_2_Pose([0, 0, 0, 0, 0, 0]))   # 单位变换（flange_space 窗口）
pose8 = invH(robot.PoseFrame()) * robot.SolveFK(purged8)
pose5 = invH(robot.PoseFrame()) * robot.SolveFK(purged5)

robot.setJoints(P7Q)
try:
    robot.MoveL(pose8)
    print('① 单位变换下 MoveL(P8位姿)：OK（TargetReachError 已消除）')
except Exception as e:
    print('① 单位变换下 MoveL(P8位姿)：仍失败 %s: %s' % (type(e).__name__, e))

# 碰撞检查：单位变换工具下，认证直线的 中点/两端 关节点是否与场景冲突
def collide(q):
    return robot.MoveJ_Test(q, q, minstep_deg=1) != 0

robot.setJoints(P5Q)
p5_start = plan[3]['joints']          # P4（翻转点）= P5 段起点
print('② 单位变换下直线端点/中点碰撞检查（P4→P5 段）：')
print('   起点P4 =', collide(p5_start))
print('   中点   =', collide([(a + b) / 2 for a, b in zip(p5_start, purged5)]))
print('   终点P5 =', collide(purged5))

robot.setPoseTool(start_tool)
robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（已恢复）')
