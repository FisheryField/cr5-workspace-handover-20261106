# -*- coding: utf-8 -*-
"""插桩：规划器跑到 P14 前视时，内部到底看到什么候选、逐项判定为何。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH, norm, pose_angle
import math

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
ns['RDK'] = RDK; ns['robot'] = robot

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json', encoding='utf-8'))
ex = ns['_retreat_orientation_records'](records)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0]*6)

E14_VALUES = tuple(ex[13]['values'])   # (100,-762,300,180,0,0)
E15_VALUES = tuple(ex[14]['values'])   # (100,-762,300,180,0,180) sing

orig_lookahead = ns['_nearest_ik_from_current_lookahead']
call_no = [0]

def wrapped_lookahead(current_q, target_pose, lookahead_ok):
    call_no[0] += 1
    p = target_pose.Pos()
    is_e14 = (abs(p[0]-E14_VALUES[0]) < 0.5 and abs(p[1]-E14_VALUES[1]) < 0.5 and abs(p[2]-E14_VALUES[2]) < 0.5)
    if not is_e14:
        return orig_lookahead(current_q, target_pose, lookahead_ok)
    cands = ns['_ik_branch_candidates'](target_pose, current_q)
    lower, upper, _ = robot.JointLimits()
    lower, upper = lower.list(), upper.list()
    nxt_target = ns['fanuc_values_to_pose'](*E15_VALUES)
    print(f'\n===== 前视调用 #{call_no[0]}（P14→P15）：当前 q = {[round(v,1) for v in current_q]}，候选 {len(cands)} 个 =====')
    for idx, c in enumerate(cands):
        verdict = 'PASS' if lookahead_ok(c) else 'fail'
        why = []
        for sgn in (180, -180):
            after = c[:]; after[5] += sgn
            if not (lower[5] <= after[5] <= upper[5]):
                why.append(f'{sgn:+d}:超限({after[5]:.0f})')
                continue
            err = invH(nxt_target) * ns['_trajectory_pose'](after)
            fk = norm(err.Pos()) <= 1e-3 and pose_angle(err) <= math.radians(.01)
            col = ns['_movej_test_cached'](c, after, 1)
            why.append(f'{sgn:+d}:限位OK,FK{fk},碰{col}')
        print(f'  cand[{idx}] = {[round(v,1) for v in c]}  内部判定={verdict}  明细[{"; ".join(why)}]')
    result = orig_lookahead(current_q, target_pose, lookahead_ok)
    print(f'  → 实际返回：{[round(v,1) for v in result]}')
    return result

ns['_nearest_ik_from_current_lookahead'] = wrapped_lookahead

def log(msg):
    s = str(msg)
    if any(k in s for k in ('前视', '救援', 'P15', 'P14', 'P13', 'P12', 'P11', '种子', '退回', '弧碰', '预检', '停顿')):
        print('  |', s)

try:
    plan = ns['_plan_continuous_trajectory'](ex, 500.0, log)
    print(f'\n=== 预检通过：{len(plan)} 段 ===')
    for k, st in enumerate(plan, 1):
        print(f'  E{k}: {st["method"]:5s} {[round(v,1) for v in st["joints"]]} note={st.get("p2p_note")}')
except ValueError as exc:
    print(f'\n=== 预检失败 ===\n  {exc}')
