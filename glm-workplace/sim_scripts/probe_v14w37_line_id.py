# -*- coding: utf-8 -*-
"""修正版：认证直线途经点在单位变换工具下的碰撞检查（只读仿真）。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
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
P4Q = list(plan[3]['joints'])
P5_rec = records[4]
target5 = ns['fanuc_values_to_pose'](*[float(v) for v in P5_rec['values'][:6]])
wps = ns['_linear_waypoints'](P4Q, target5)
print('P4→P5 认证直线途经点数 =', len(wps))

robot.setPoseTool(Fanuc_2_Pose([0, 0, 0, 0, 0, 0]))
hits = 0
for k, q in enumerate(wps):
    if robot.MoveJ_Test(q, q, minstep_deg=1) != 0:
        hits += 1
        print('  途经点 %d/%d 碰撞！关节=%s' % (k + 1, len(wps), ['%.2f' % v for v in q]))
print('单位变换下直线途经点碰撞数 = %d / %d' % (hits, len(wps)))

robot.setPoseTool(start_tool)
robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（已恢复）')
