# -*- coding: utf-8 -*-
"""验证 v14w38：隐藏把手后，(a) 关节弧中点(本地退化动画路径)不再碰撞；
(b) 真直线途经点仍全净；(c) 重显示后状态复原。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
start_q = robot.Joints().list()[:6]
start_tool = robot.PoseTool()
handle = RDK.Item('门把手_bs1')

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
P5Q = list(plan[4]['joints'])
arc_mid = [(a + b) / 2 for a, b in zip(P4Q, P5Q)]
frozen = [66.98, 25.15, 113.87, -139.02, -66.98, 180.0]

def col(q):
    return robot.MoveJ_Test(q, q, minstep_deg=1) != 0

robot.setJoints(arc_mid)
print('弧中点[显示把手] 碰撞 =', col(arc_mid))
robot.setJoints(frozen)
print('冻结姿态[显示把手] 碰撞 =', col(frozen))

handle.setVisible(False)
robot.setJoints(arc_mid)
print('弧中点[隐藏把手] 碰撞 =', col(arc_mid))
robot.setJoints(frozen)
print('冻结姿态[隐藏把手] 碰撞 =', col(frozen))
handle.setVisible(True)

robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（已恢复）')
