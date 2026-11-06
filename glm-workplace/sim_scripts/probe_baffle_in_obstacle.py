# -*- coding: utf-8 -*-
"""反证测试：证明『挡板_半封闭3面』确实参与避障计算（只读+仿真，不动实机）。
方法：取一个明确落在侧板 AABB 内的 TCP 目标（工具尖端穿过侧板平面 x=-215），
按宏同款流程启用障碍物碰撞对后跑 MoveJ_Test —— 期望：非零返回 +
_collision_details() 中出现『挡板_半封闭3面』。
再做 A/B：临时关掉挡板碰撞对复测 —— 期望：通过（证明拦路的正是挡板）。
"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
BAFFLE = '挡板_半封闭3面'
BAFFLE_BOX = dict(x=(-235.0, -215.0), y=(-1106.0, -806.0), z=(0.0, 710.0))

# 目标：工具尖端 (x, y, z) 落在侧板体积内；姿态取作业同款 [90,0,0]（工具沿 -y 伸出，
# 法兰在 TCP +y 159.6 处 —— 法兰可达性由 y 决定，取 y=-880 使法兰 ≈ -720 在臂展内）
CANDIDATES = [
    (-225.0, -880.0, 300.0, 90.0, 0.0, 0.0),
    (-225.0, -860.0, 250.0, 90.0, 0.0, 0.0),
    (-228.0, -840.0, 350.0, 90.0, 0.0, 0.0),
    (-225.0, -830.0, 300.0, 90.0, 0.0, 0.0),
]
start = [0.0] * 6

def inside_box(v):
    return (BAFFLE_BOX['x'][0] <= v[0] <= BAFFLE_BOX['x'][1]
            and BAFFLE_BOX['y'][0] <= v[1] <= BAFFLE_BOX['y'][1]
            and BAFFLE_BOX['z'][0] <= v[2] <= BAFFLE_BOX['z'][1])

end = None
pose_ok = None
for vals in CANDIDATES:
    print('候选 TCP:', vals, '在侧板体积内 =', inside_box(vals))
    pose = Fanuc_2_Pose(list(vals))
    try:
        q = robot.SolveIK(pose, tool=robot.PoseTool(), reference=robot.PoseFrame())
    except Exception as e:
        print('   IK 失败:', e)
        continue
    q = list(q)[:6]
    if isinstance(q[0], (list, tuple)):
        q = list(q[0])[:6]
    q = [float(v) for v in q]
    print('   IK 关节:', ['%.2f' % v for v in q])
    end, pose_ok = q, vals
    break
assert end is not None, '所有候选均 IK 失败（都不可达）'

# 按宏同款启用障碍物（含挡板）
ns['_enable_obstacle_checks']()
print('\n障碍物已启用（元组含挡板）：', ns.get('MOVL_DIRECT_MAX_MM') is not None)

robot.setJoints(start)
status = robot.MoveJ_Test(start, end, minstep_deg=1)
details = ns['_collision_details']()
print('\n[A] 挡板碰撞对 ON：MoveJ_Test =', status)
print('    details =', details[:400])
hit_baffle = BAFFLE in details

# A/B：关掉挡板与【连杆+工具】的全部碰撞对（与宏的启用逻辑镜像），复测
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL
baf = RDK.Item(BAFFLE, ITEM_TYPE_OBJECT)
assert baf.Valid(), '站内缺少挡板'
for link in range(1, 7):
    RDK.setCollisionActivePair(0, robot, baf, link, 0)
for tool in RDK.ItemList(ITEM_TYPE_TOOL):
    RDK.setCollisionActivePair(0, tool, baf)
robot.setJoints(start)
status2 = robot.MoveJ_Test(start, end, minstep_deg=1)
details2 = ns['_collision_details']()
print('\n[B] 挡板碰撞对全关（连杆+工具）：MoveJ_Test =', status2)
print('    details =', details2[:400])

print()
if hit_baffle and status != 0 and (status2 == 0 or BAFFLE not in details2):
    print('RESULT: PASS —— 挡板 ON 时被拦且点名挡板；OFF 后放行 ⇒ 挡板确实参与避障计算')
else:
    print('RESULT: 需人工判读  hit_baffle=%s status=%s status2=%s' % (hit_baffle, status, status2))
