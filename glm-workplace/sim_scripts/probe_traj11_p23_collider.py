# -*- coding: utf-8 -*-
"""轨迹11 在 P2P 规划器 + 新场景下的失败点取证：
环形记录 _collision_details 的返回值，规划失败时打印最后若干条，
定位 P23 换向失败的真实碰撞对象。只读仿真，不碰实机。"""
import sys, io, json, traceback
from collections import deque
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))

# 插桩：环形记录最近的碰撞详情
_ring = deque(maxlen=40)
_orig = ns['_collision_details']
def _wrapped():
    d = _orig()
    _ring.append(d)
    return d
ns['_collision_details'] = _wrapped

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹11.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)
robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
_last = []
def log(m):
    _last.append(str(m))
    if '种子' in m or 'P23' in m or '碰撞' in m:
        print('  |', m)
try:
    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
    print('未失败（%d 段）' % len(plan))
except Exception as e:
    print('\n=== 失败 ===')
    print(type(e).__name__ + ':', e)
    print('\n最后 %d 条碰撞详情（最可能=P23 两方向的真实碰撞对象）：' % len(_ring))
    seen = []
    for d in _ring:
        if d not in seen:
            seen.append(d)
    for d in seen[-8:]:
        print('   *', d)
    print('\n最后3条规划日志：')
    for m in _last[-3:]:
        print('   ', m[:180])
