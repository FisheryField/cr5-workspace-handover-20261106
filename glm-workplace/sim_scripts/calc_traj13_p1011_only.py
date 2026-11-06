# -*- coding: utf-8 -*-
"""对照试验：traj13@tool126，只降 P10/P11 至460（其余保持原z）→ 整段预检。
原版不动，生成另一临时副本。"""
import sys, io, json, copy, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
print('PoseTool =', robot.PoseTool().Pos())

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)

records = json.load(open(SRC, encoding='utf-8'))
out = copy.deepcopy(records)
for k in (9, 10):   # P10, P11 (0-based)
    assert abs(float(out[k]['values'][2]) - 470.0) < 1e-6, out[k]
    out[k]['values'][2] = 460.0
TMP = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13_t126_p1011only.json'
open(TMP, 'w', encoding='utf-8').write(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
print('临时副本 =', TMP)

records2 = ns['_retreat_orientation_records'](out)
robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
def log(m):
    print('  |', m)
try:
    plan = ns['_plan_continuous_trajectory'](records2, 500.0, log)
    print('\n=== 预检通过：%d 段 ===' % len(plan))
    print('RESULT: PASS')
except ValueError as exc:
    print('\n=== 预检失败 ===')
    print(' ', exc)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
