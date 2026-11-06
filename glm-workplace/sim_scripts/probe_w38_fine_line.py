# -*- coding: utf-8 -*-
"""v14w37 冻死复检：单位变换窗口下，MoveL_Test(1mm) 检查直发直线的真实动画路径；
若碰撞，隐藏把手后复测（验证 v14w38 隐藏方案）。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

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

def line_test(tag, start_q_seg, end_q_seg):
    purged, _ = ns['_movl_digit_safe_joints'](end_q_seg)
    robot.setPoseTool(Fanuc_2_Pose([0, 0, 0, 0, 0, 0]))
    pose = invH(robot.PoseFrame()) * robot.SolveFK(purged)
    r = robot.MoveL_Test(start_q_seg, pose, minstep_mm=1)
    print('%s MoveL_Test(1mm)=%s' % (tag, r))
    if r != 0:
        print('   碰撞处模型关节 =', ['%.2f' % v for v in robot.Joints().list()[:6]])
    return r

r_p5 = line_test('P4→P5(200mm,rx90)', list(plan[3]['joints']), list(plan[4]['joints']))
r_p3 = line_test('P2→P3(100mm,rx-90)', list(plan[1]['joints']), list(plan[2]['joints']))

if r_p5 != 0 or r_p3 != 0:
    print('--- 隐藏把手后复测 ---')
    try:
        handle.Hide(True)
        if r_p5 != 0:
            line_test('P4→P5[隐藏]', list(plan[3]['joints']), list(plan[4]['joints']))
        if r_p3 != 0:
            line_test('P2→P3[隐藏]', list(plan[1]['joints']), list(plan[2]['joints']))
    finally:
        handle.Hide(False)

robot.setPoseTool(start_tool)
robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（已恢复）')
