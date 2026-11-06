# -*- coding: utf-8 -*-
"""离线复现 18:44 单点 MoveL 预检死亡：只做仿真侧调用，不连控制器、不发运动指令。
复刻链路：_enable_obstacle_checks -> MoveJ_Test(start,start) -> _linear_path_endpoint
          (MoveL_Test 10mm/1mm -> AddProgram+MoveL+InstructionListJoints(OFF))
每步先落盘再执行，死在哪一步一目了然。
"""
import io, time, sys, math

LOG = r'D:\mydata\glm-workplace\sim_scripts\repro_1844_log.txt'
STEP = {'n': 0}

def log(s):
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write(time.strftime('%H:%M:%S') + ' | ' + s + '\n')

def step(msg):
    STEP['n'] += 1
    log('[step %d] %s' % (STEP['n'], msg))

log('===== repro start, pid=%d =====' % __import__('os').getpid())

# 18:44 死亡发生于预检早期（“开始预检”后无任何分支日志），据此扩展复现：
# 覆盖 MoveJ 兑底选解分支（_obstacle_joint_target_uncached 逐步复刻）。
REPRO_DEEP = '--deep' in sys.argv
if not REPRO_DEEP:
    log('（浅模式，仅主链；本次运行结束）')
    sys.exit(0)

step('import robodk')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, RUNMODE_SIMULATE, COLLISION_ON, COLLISION_OFF
from robodk.robomath import Fanuc_2_Pose, invH

step('Robolink() 连接 RoboDK API')
RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
step('robot = %s valid=%s' % (robot.Name(), robot.Valid()))

step('setRunMode(RUNMODE_SIMULATE)')
RDK.setRunMode(RUNMODE_SIMULATE)
RDK.Command('Trace', 'Off')

# 18:44:23 实测起点（@192）
start = [16.38, -34.90, -44.95, 169.85, -90.00, 106.38]
# 18:44:21 目标
vals = [0.0, -775.0, 300.0, -90.0, 0.0, 180.0]

step('setJoints(start)')
robot.setJoints(start)

step('_enable_obstacle_checks 复刻')
for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40'):
    obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
    step('obstacle %s valid=%s' % (name, obstacle.Valid()))
    if not obstacle.Valid():
        continue
    if name == '安装台_650x650x80mm':
        r = RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0)
        step('  pair off base ret=%s' % r)
    for link in range(1, 7):
        r = RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0)
    step('  links 1-6 pairs on')
    for tool in RDK.ItemList(ITEM_TYPE_TOOL):
        parent = tool.Parent()
        while parent.Valid() and parent.item != robot.item:
            parent = parent.Parent()
        if parent.Valid():
            RDK.setCollisionActivePair(COLLISION_ON, tool, obstacle)
    step('  tool pairs on')
step('setCollisionActive(ON)')
RDK.setCollisionActive(COLLISION_ON)

step('MoveJ_Test(start,start) 起始姿态检查')
st = robot.MoveJ_Test(start, start, minstep_deg=1)
step('  -> %s' % st)

step('fanuc_to_pose(target)')
target = Fanuc_2_Pose(list(vals))
step('MoveL_Test 10mm 粗筛')
st = robot.MoveL_Test(start, target, minstep_mm=10)
step('  -> %s' % st)
if st != 0:
    log('粗筛即失败（进程未死）——按 18:44 实际路径，接下来是 MoveJ 兑底选解分支，继续复现')

# ===== 以下复刻 _obstacle_joint_target_uncached 深层链 =====
step('JointLimits()')
lower, upper, _ = robot.JointLimits()
lower, upper = lower.list(), upper.list()
step('  lower=%s upper=%s' % ([round(v,1) for v in lower], [round(v,1) for v in upper]))

step('SolveIK_All（候选生成，含 J6 圈数扩展）')
from robodk.robomath import Pose_2_Fanuc
from robodk.robolink import ITEM_TYPE_PROGRAM
# 复刻 _tcp_target_to_flange + fanuc_values_to_pose 的合成：目标位姿直接用 Fanuc_2_Pose
solutions = robot.SolveIK_All(target)
step('  -> %d 个解' % len(solutions.rows))

step('SolveIK_All 结果转列表（含 J6 圈数扩展）')
sol_list = [list(map(float, sol[:6])) for sol in solutions.rows]
candidates = []
for solution in sol_list:
    q = [((float(v) + 180.0) % 360.0) - 180.0 for v in solution[:6]]
    if len(q) != 6:
        continue
    for turns6 in (0, -1, 1):
        candidate = q[:]
        candidate[5] += 360.0 * turns6
        if all(lower[j] <= candidate[j] <= upper[j] for j in range(6)):
            if not any(max(abs(a-b) for a, b in zip(candidate, old)) < 1e-6 for old in candidates):
                candidates.append(candidate)
step('  扩展后候选 %d 个' % len(candidates))
for idx, cand in enumerate(candidates[:5]):
    step('  cand[%d] = %s' % (idx, [round(v,1) for v in cand]))

step('排序前 FK 采样（_obstacle_posture_key / JointPoses）')
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
base_to_table = invH(table.PoseAbs()) * robot.PoseAbs()
saved = robot.Joints().list()[:6]
try:
    for end in candidates[:8]:
        elbow = invH(table.PoseAbs()) * robot.PoseAbs() * robot.JointPoses(end)[3]
        h = elbow.Pos()[2]
        step('  FK cand h=%.1f' % h)
finally:
    robot.setJoints(saved)
step('FK 采样完毕，进程存活')

# ===== 补齐宏预检后半段：排序 + 偏离复核 + MoveJ_Test(0.25°) + 整段碰撞复核 =====
step('排序+偏离复核+_check_movej_tcp_trajectory 复刻（前8个候选）')
a = None
ranked = []
for end in candidates:
    deviation, height = 0.0, float('inf')
    # 复刻 _tcp_position_from_joints：invH(PoseFrame)*SolveFK(q)*PoseTool → 位置
    for k in range(11):
        q = [x + (y-x)*k/10 for x, y in zip(start, end)]
        fk = invH(robot.PoseFrame()) * robot.SolveFK(q) * robot.PoseTool()
        p = fk.Pos()
        # 点到线段距离（起点a-目标vals[:3]）
        if a is None:
            a0 = (invH(robot.PoseFrame()) * robot.SolveFK(start) * robot.PoseTool()).Pos()
            a = a0
        ax, ay, az = a; bx, by, bz = vals[:3]; px, py, pz = p
        ab = (bx-ax, by-ay, bz-az); ap = (px-ax, py-ay, pz-az)
        ab2 = sum(v*v for v in ab)
        t = max(0.0, min(1.0, sum(u*v for u, v in zip(ap, ab))/ab2)) if ab2 > 1e-12 else 0.0
        qq = (ax+t*ab[0], ay+t*ab[1], az+t*ab[2])
        d = math.sqrt((px-qq[0])**2 + (py-qq[1])**2 + (pz-qq[2])**2)
        deviation = max(deviation, d)
        jp = robot.JointPoses(q)[3]
        h = (base_to_table * jp).Pos()[2]
        height = min(height, h)
    ranked.append(((int(deviation/20), -height, sum(abs(y-x) for x, y in zip(start, end))), end))
ranked.sort(key=lambda e: e[0])
step('  排序完成，前5：')
for _, e in ranked[:5]:
    step('    %s' % [round(v,1) for v in e])

found = None
for idx, (_, end) in enumerate(ranked):
    step('MoveJ_Test 精查候选 %d/%d：minstep=0.25°' % (idx+1, len(ranked)))
    r = robot.MoveJ_Test(start, end, minstep_deg=0.25)
    step('  -> %s' % r)
    if r == 0:
        found = end
        break
step('found = %s' % ([round(v,2) for v in found] if found else None))

if found:
    step('整段碰撞复核复刻：InstructionListJoints(collision=ON)')
    prog = RDK.AddProgram('_repro_整段复核', robot)
    try:
        prog.setVisible(False)
        prog.setPoseFrame(robot.PoseFrame())
        prog.setPoseTool(robot.PoseTool())
        prog.MoveJ(start)
        prog.MoveJ(found)
        msg, matrix, status = prog.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        step('  -> status=%s msg=%r' % (status, (msg or '')[:150]))
    finally:
        prog.Delete()

log('===== repro 全链（含后半段）走完，进程未死 =====')
step('MoveL_Test 1mm 细查（碰撞开）')
st = robot.MoveL_Test(start, target, minstep_mm=1)
step('  -> %s' % st)

step('AddProgram 提取终点（InstructionListJoints, 碰撞关）')
program = RDK.AddProgram('_repro_路径预检', robot)
try:
    program.setVisible(False)
    robot.setJoints(start)
    program.setPoseFrame(robot.PoseFrame())
    program.setPoseTool(robot.PoseTool())
    step('program.MoveJ(start)')
    program.MoveJ(start)
    step('program.MoveL(target)')
    program.MoveL(target)
    step('InstructionListJoints(mm=1,deg=1,collision=OFF)')
    message, matrix, status = program.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_OFF)
    step('  -> status=%s msg=%r rows=%s' % (status, message[:120] if message else '', matrix.rows if hasattr(matrix, 'rows') else '?'))
    end = matrix.tr().rows[-1][:6]
    step('end joints = %s' % [round(v, 3) for v in end])
finally:
    program.Delete()
    step('program.Delete() done')

log('===== repro 全链走完，进程未死：预检调用本身不杀人 =====')
