# -*- coding: utf-8 -*-
"""复现 P8 的 TargetReachError（只读仿真；结束恢复关节/runmode）。
流程：整段规划取 P7/P8 认证关节 → 模型摆到 P7（=执行到 P7 的状态）→
净化 P8 → 依次单测 ①SolveFK(purged) ②MoveL(法兰位姿) ③对照 MoveL(关节)，
看哪一步抛 TargetReachError。"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()
start_q = robot.Joints().list()[:6]

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹14.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0] * 6)

plan = ns['_plan_continuous_trajectory'](records, 500.0, lambda m: None)
P7Q = list(plan[6]['joints'])
P8Q = list(plan[7]['joints'])
purged, pnote = ns['_movl_digit_safe_joints'](P8Q)
print('P7 认证关节 =', ['%.4f' % v for v in P7Q])
print('P8 认证关节 =', ['%.4f' % v for v in P8Q])
print('P8 净化结果 =', (['%.4f' % v for v in purged] if purged else None), '|', pnote)
lo, hi, _ = robot.JointLimits()
lo_l, hi_l = lo.list(), hi.list()
print('模型限位 lower =', lo_l)
print('模型限位 upper =', hi_l)
for j in range(6):
    if purged and not (lo_l[j] <= purged[j] <= hi_l[j]):
        print('  !! 轴%d 超模型限位: %.4f' % (j + 1, purged[j]))

robot.setJoints(P7Q)   # 模型摆到 P7（复现执行现场）

def step(name, fn):
    try:
        r = fn()
        print('[%s] OK -> %s' % (name, r))
        return r
    except Exception as e:
        print('[%s] 抛异常: %s: %s' % (name, type(e).__name__, e))
        return None

pose = step('① SolveFK(purged)', lambda: invH(robot.PoseFrame()) * robot.SolveFK(purged))
if pose is not None:
    print('   位姿 Pos =', ['%.4f' % v for v in pose.Pos()])
    step('② MoveL(位姿) [SIMULATE]', lambda: robot.MoveL(pose) or 'moved')
    robot.setJoints(P7Q)   # 摆回 P7 再测对照
step('③ MoveL(关节) 对照 [SIMULATE]', lambda: robot.MoveL(purged) or 'moved')

robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（已恢复）')
