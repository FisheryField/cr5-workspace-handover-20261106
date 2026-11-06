# -*- coding: utf-8 -*-
"""临时验证（只读母本）：执行 _tmp_v14w34_patched.py 的头部，跑轨迹14 完整预检，
打印每点 method/note/途经点数；断言 P7 变为单条 MoveJ（同位姿换姿MoveJ直达）。
"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
start_joints = robot.Joints().list()[:6]

src = open(r'D:\mydata\glm-workplace\sim_scripts\_tmp_v14w34_patched.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_patched_head', 'exec'), ns)
print('LOG_VERSION(临时补丁) =', ns.get('LOG_VERSION'))

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹14.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)
print('执行点数 =', len(records))

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
    robot.setJoints(start_joints)
    sys.exit(1)

print('\n=== 预检通过：%d 段 ===' % len(plan))
print('\n点号 method                途经点 note')
for k, step in enumerate(plan, 1):
    wps = step.get('waypoints') or []
    flag = ''
    if k in (6, 7, 8):
        flag = '   <== 关注'
    print('P%-2d  %-18s %3d    %s%s' % (k, step['method'], len(wps), step.get('p2p_note', ''), flag))

p7 = plan[6]
ok = (p7['method'] == 'MoveJ' and not (p7.get('waypoints') or [])
      and 'MoveJ' in (p7.get('p2p_note') or ''))
print('\nP7 单条 MoveJ 直达 = %s' % ('PASS ✓' if ok else 'FAIL ✗ (note=%s, method=%s, wps=%d)' % (
    p7.get('p2p_note'), p7['method'], len(p7.get('waypoints') or []))))
total_wps = sum(len(s.get('waypoints') or []) for s in plan)
print('全轨迹途经点总数 =', total_wps)

RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
robot.setJoints(start_joints)
print('DONE（只读母本；runmode/关节已恢复）')
sys.exit(0 if ok else 2)
