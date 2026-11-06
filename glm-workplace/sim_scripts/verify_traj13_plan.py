# -*- coding: utf-8 -*-
"""连续轨迹13（原版）离线 P2P 预检（只读）。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))
print('PoseTool =', robot.PoseTool().Pos())

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹13.json', encoding='utf-8'))
print('录入点数 =', len(records))
records = ns['_retreat_orientation_records'](records)
print('展开后执行点数 =', len(records))

robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def log(msg):
    print('  |', msg)

try:
    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
except ValueError as exc:
    print('\n=== 预检失败 ===')
    print(' ', exc)
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
    sys.exit(1)

print('\n=== 预检通过：%d 段 ===' % len(plan))
print('\n点号 method                途经点 note')
for k, step in enumerate(plan, 1):
    wps = step.get('waypoints') or []
    print('P%-2d  %-18s %3d    %s' % (k, step['method'], len(wps), step.get('p2p_note', '')))
print('\nRESULT: PASS')
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（runmode 已复位）')
