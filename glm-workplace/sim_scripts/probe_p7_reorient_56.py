# -*- coding: utf-8 -*-
"""只读诊断：轨迹14 P6→P7（同位姿 rx90→180 换姿）为何仍落 MoveL 细分 56 跳。
复现宏 v14w33 的三段决策：
  A) _seg_mm_ro <= 1.0 阈值是否成立（不成立则 2058/2072 两个搜索根本不会跑）
  B) 固定 P6 构型下，P7 全分支 MoveJ 是否有解（2058 搜索）
  C) v14w33d 回改：任意 P6 分支 × 任意 P7 分支（含 P5→P6 连通性）是否有解
不发任何实机指令；结束恢复 RUNMODE_RUN_ROBOT 与起始关节。
"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH, norm

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
start_joints = robot.Joints().list()[:6]

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹14.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)

def find_idx(vals):
    for k, r in enumerate(records):
        if r['type'] == 'TCP' and all(abs(float(r['values'][j]) - vals[j]) < 1e-9 for j in range(6)):
            return k
    raise SystemExit('point not found: %s' % (vals,))

P4_V = [None]  # 占位，稍后按记录找 P4：由 P5 前一点推断
i5 = find_idx([0.0, -719.0, 380.0, 90.0, 0.0, 0.0])
i6 = find_idx([0.0, -650.0, 380.0, 90.0, 0.0, 0.0])
i7 = find_idx([0.0, -650.0, 380.0, 180.0, 0.0, 0.0])
print('idx P5/P6/P7 =', i5 + 1, i6 + 1, i7 + 1, '（1-based）')

# 14:19 实跑（种子7）P4/P6 执行关节 —— 取自 real_gui_log_p2p.txt
P4_Q = [-58.74371018517957, -26.060110461966048, -112.2492115297517,
        138.30932199171772, 58.74371018517957, 180.0]
P6_Q = [-67.43858771971193, -17.80254851667152, -126.39845591028943,
        144.20100442696094, 67.43858771971193, 180.0]

robot.setJoints(P6_Q)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

traj = ns['_trajectory_pose']
ik_branches = ns['_ik_branch_candidates']
mj = ns['_movej_test_cached']
interfere = ns['_real_interfere_combo']
limit_ok = ns['_real_limit_ok']
lower, upper, _ = robot.JointLimits()
lower, upper = lower.list(), upper.list()
rec6, rec7 = records[i6], records[i7]
pose6 = Fanuc_2_Pose([float(v) for v in rec6['values'][:6]])
pose7 = Fanuc_2_Pose([float(v) for v in rec7['values'][:6]])

print('\n=== A) v14w33 阈值 _seg_mm_ro ===')
seg_mm = norm((traj(P6_Q) * invH(pose7)).Pos())
print('FK(P6实跑关节) vs P7目标 位置差 = %.6f mm  -> %s' %
      (seg_mm, '≤1.0 搜索会跑' if seg_mm <= 1.0 else '>1.0 搜索被跳过（阈值问题）'))

print('\n=== B) 固定 P6 构型：P7 全分支单条 MoveJ ===')
c7_list = ik_branches(pose7, P6_Q)
print('P7 分支候选数 =', len(c7_list))
pass_fixed = []
for n, c7 in enumerate(c7_list, 1):
    why = []
    if interfere(c7):
        why.append('J4×J5组合禁区')
    if not limit_ok(c7, lower, upper):
        why.append('超限')
    if why:
        print('  cand%-2d %s -> 拒：%s' % (n, ['%.1f' % v for v in c7], '、'.join(why)))
        continue
    r = mj(P6_Q, c7, 1)
    if r == 0:
        pass_fixed.append(c7)
        print('  cand%-2d %s -> ✓ 无碰单条 MoveJ' % (n, ['%.1f' % v for v in c7]))
    else:
        print('  cand%-2d %s -> MoveJ弧碰(码%s)' % (n, ['%.1f' % v for v in c7], r))
print('固定 P6 下可用分支数 =', len(pass_fixed))

print('\n=== C) v14w33d 回改：P6 全分支 × P7 全分支（含 P5→P6 连通） ===')
# P5 规划关节 = 强制 MoveL 段的直线末端 IK（与宏 1968 同款）
pose5 = Fanuc_2_Pose([float(v) for v in records[i5]['values'][:6]])
p5_end, p5_detail = ns['_linear_path_endpoint'](P4_Q, pose5)
if p5_end is None:
    print('P5 直线末端求解失败：', p5_detail)
    P5_Q = None
else:
    P5_Q = list(p5_end)
    print('P5 规划关节 =', ['%.2f' % v for v in P5_Q])

c6_list = ik_branches(pose6, P5_Q if P5_Q is not None else P6_Q)
print('P6 分支候选数 =', len(c6_list))
pairs_ok = 0
pair_sample = []
for c6 in sorted(c6_list, key=lambda c: sum((c[j] - P6_Q[j]) ** 2 for j in range(6))):
    tag = ['%.1f' % v for v in c6]
    if interfere(c6):
        print('  c6 %s -> 拒：J4×J5组合禁区' % tag)
        continue
    if not limit_ok(c6, lower, upper):
        print('  c6 %s -> 拒：超限' % tag)
        continue
    if P5_Q is not None and mj(P5_Q, c6, 1) != 0:
        print('  c6 %s -> 拒：P5→P6 弧碰' % tag)
        continue
    ok_here = 0
    for c7 in c7_list:
        if interfere(c7) or not limit_ok(c7, lower, upper):
            continue
        if mj(c6, c7, 1) == 0:
            ok_here += 1
            pairs_ok += 1
            if len(pair_sample) < 6:
                pair_sample.append((tag, ['%.1f' % v for v in c7]))
    print('  c6 %s -> 与其可贯通的 P7 分支数 = %d' % (tag, ok_here))
print('总可用 (c6,c7) 对 =', pairs_ok)
for a, b in pair_sample:
    print('   样本对：P6=%s -> P7=%s' % (a, b))

# 恢复
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
robot.setJoints(start_joints)
print('\nDONE（只读；runmode 已恢复 RUN_ROBOT，关节已复位）')
