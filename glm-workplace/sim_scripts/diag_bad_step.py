# -*- coding: utf-8 -*-
"""定位：重规划 traj13，逐段打印关节并检测超模型限位/SolveFK 失败的段。"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹13.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)
robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
plan = ns['_plan_continuous_trajectory'](records, 500.0, lambda m: None)
lower, upper, _ = robot.JointLimits()
lower, upper = lower.list(), upper.list()
print('模型限位：', [round(v, 1) for v in lower[:6]], [round(v, 1) for v in upper[:6]])
for i, step in enumerate(plan, 1):
    q = step['joints']
    bad = [j for j in range(6) if not lower[j] <= q[j] <= upper[j]]
    fk_ok = True
    try:
        robot.SolveFK(q)
    except Exception:
        fk_ok = False
    mark = ''
    if bad or not fk_ok:
        mark = '  <<< 超限关节=%s FK=%s' % (bad, fk_ok)
    print('%2d %-5s %-14s q=[%s]%s' % (i, step['method'], step['p2p_note'][:14],
                                       ', '.join('%.2f' % v for v in q), mark))
