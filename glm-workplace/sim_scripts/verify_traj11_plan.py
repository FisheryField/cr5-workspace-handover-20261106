# -*- coding: utf-8 -*-
"""连续轨迹14（=轨迹13 类型 · tool=182 适配版：6 个 rx=180 高点 z−82，其余原样）离线评估（只读，不起 GUI、不动实机）：
1) 与实跑同流程：_retreat_orientation_records 展开 → _plan_continuous_trajectory 预检（起点全零）；
2) 逐段标注：方法/备注/段长/姿态变化，判定 v14w 直发门禁（MoveL 细分 + ≤150mm + 姿态≤0.5°）；
3) 对过门禁的段直接调用 _movl_digit_safe_joints，报告哪些段会被净化、净化结果。
通过标准：预检不抛 ValueError（= _verify_obstacle_plan 全绿）。
"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))
fixed = ns['_ensure_canonical_tool']()
print('工具守护 =', '已自动恢复 [0,0,182]' if fixed else '正常(182)')

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹14.json', encoding='utf-8'))
print('录入点数 =', len(records))
records = ns['_retreat_orientation_records'](records)
print('展开后执行点数 =', len(records))

robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
plan_fn = ns['_plan_continuous_trajectory']
def log(msg):
    print('  |', msg)
try:
    plan = plan_fn(records, 500.0, log)
except ValueError as exc:
    print('\n=== 预检失败 ===')
    print(' ', exc)
    sys.exit(1)
print('\n=== 预检通过：%d 段 ===' % len(plan))

_traj = ns['_trajectory_pose']
purge = ns['_movl_digit_safe_joints']
direct_cnt = purge_cnt = 0
prev = [0.0] * 6
print('\n段号 method 直发? 段长mm 姿态°  净化  note / 目标关节')
for k, step in enumerate(plan, 1):
    method = step['method']
    wps = step.get('waypoints') or []
    seg_mm = seg_rot = None
    if method == 'MoveL' and wps:
        rel = _traj(step['joints']) * ns['invH'](_traj(prev))
        seg_mm, seg_rot = ns['norm'](rel.Pos()), ns['pose_angle'](rel)
    gate = (method == 'MoveL' and bool(wps) and seg_mm is not None
            and seg_mm <= ns['MOVL_DIRECT_MAX_MM']
            and seg_rot <= math.radians(0.5))
    purge_note = '-'
    if gate:
        direct_cnt += 1
        send_q, note = purge(step['joints'])
        if send_q is None:
            purge_note = '失败→细分'
        elif note:
            purge_cnt += 1
            purge_note = '净化:' + note[:60]
        else:
            purge_note = '免净化'
    print('  段%-2d %-5s %-4s %s %s  %-4s  %s' % (
        k, method, '✓' if gate else '',
        ('%6.1f' % seg_mm) if seg_mm is not None else '     -',
        ('%5.2f' % math.degrees(seg_rot)) if seg_rot is not None else '   -',
        purge_note,
        step['p2p_note'][:38]))
    prev = step['joints']

print('\n统计：直发资格段 %d / %d；其中需净化 %d；净化失败 %d' % (
    direct_cnt, len(plan), purge_cnt, 0))
print('RESULT: PASS（预检全绿）')
