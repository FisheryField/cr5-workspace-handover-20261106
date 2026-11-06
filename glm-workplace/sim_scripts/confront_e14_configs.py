# -*- coding: utf-8 -*-
"""对质实验：TCP仿真成功方案里 E14(段14) 的完整构型 vs 我的分支判定（只读）。
回答：它那个构型在我同款 FK/碰撞判定下能不能过 ±180 换向？
"""
import sys, io, json, ast as _ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH, norm, pose_angle
import math

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

# ---- 载入 P2P 母本函数 ----
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
ns['RDK'] = RDK; ns['robot'] = robot

# ---- 载入 TCP仿真 函数并跑其规划器拿成功 plan ----
sim_src = open(r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump\TCP仿真_station_export.py', encoding='utf-8').read()
sim_ns = {}
tree = _ast.parse(sim_src)
keep = [n for n in tree.body if isinstance(n, (_ast.FunctionDef, _ast.Import, _ast.ImportFrom, _ast.If))
        or (isinstance(n, _ast.Assign) and isinstance(n.targets[0], _ast.Name)
            and n.targets[0].id not in ('RDK', 'robot'))]
sim_ns = {'Robolink': robolink.Robolink, 'robot': robot}
exec(compile(_ast.Module(body=keep, type_ignores=[]), 'sim_funcs', 'exec'), sim_ns)
sim_ns['RDK'] = RDK

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json', encoding='utf-8'))
ex = ns['_retreat_orientation_records'](records)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0]*6)
silent = lambda msg: None
plan = sim_ns['_plan_continuous_trajectory'](ex, 500.0, silent)
print(f'TCP仿真 plan {len(plan)} 段，全绿')

E14 = plan[13]['joints'][:6]
E15rec = ex[14]
print(f'\nTCP仿真 E14 构型 =', [round(v, 2) for v in E14])
print(f'E15 奇异记录 = {E15rec["values"]} delta={E15rec.get("j6_delta")}')

# ---- 用 P2P 母本的同款判定复核 ----
ns['_enable_obstacle_checks']()
lower, upper, _ = robot.JointLimits()
lower, upper = lower.list(), upper.list()
nxt_target = ns['fanuc_values_to_pose'](*E15rec['values'])
for sgn in (180, -180):
    after = E14[:]; after[5] += sgn
    err = invH(nxt_target) * ns['_trajectory_pose'](after)
    fk_ok = norm(err.Pos()) <= 1e-3 and pose_angle(err) <= math.radians(.01)
    in_lim = lower[5] <= after[5] <= upper[5]
    st = ns['_movej_test_cached'](E14, after, 1)
    print(f'  方向{sgn:+d}: J6->{after[5]:+.1f} 限位={in_lim} FK={fk_ok} MoveJ_Test={st}')

# ---- 该位姿在我的候选枚举里吗？----
cands = ns['_ik_branch_candidates'](ns['fanuc_values_to_pose'](*ex[13]['values']), E14)
match = [c for c in cands if max(abs(a-b) for a, b in zip(c, E14)) < 1e-6]
print(f'\nP2P候选集中含TCP仿真的E14构型：{bool(match)}（候选总数 {len(cands)}）')
# 在候选上逐个跑 lookahead 三条件
passing = []
for c in cands:
    for sgn in (180, -180):
        after = c[:]; after[5] += sgn
        if not (lower[5] <= after[5] <= upper[5]):
            continue
        err = invH(nxt_target) * ns['_trajectory_pose'](after)
        if norm(err.Pos()) > 1e-3 or pose_angle(err) > math.radians(.01):
            continue
        if ns['_movej_test_cached'](c, after, 1) == 0:
            passing.append((c[:], sgn))
print(f'满足前视三条件的（分支,方向）：{len(passing)} 组')
for c, sgn in passing[:5]:
    print('   ', [round(v, 1) for v in c], f'{sgn:+d}')
