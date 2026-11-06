#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原点 -> P1 -> P2 -> P3 -> P4(奇异点) -> P5 -> P6 -> P7 -> P8(奇异点) -> P9 -> P10
单步运动测试（GUI，TCP 坐标版；带【台面/地面】碰撞预检 + 自动换解）

P1 / P2 = **轨迹3（连续轨迹3.json）的第 1、2 个点**，原样就是 TCP（法兰 Fanuc 六数）；
P3 / P5 / P6 / P7 / P9 / P10 = 后续新增的普通 TCP 点；**P4 / P8 = 奇异点**（只走关节运动）：
    P1  =  500.0,   0.0, 300.0, 180.0,  0.0,   0.0
    P2  =    0.0, -775.0, 300.0, -90.0, 0.0, 180.0
    P3  =  100.0, -775.0, 300.0, -90.0, 0.0, 180.0
    P4  =  100.0, -775.0, 300.0, -90.0, 0.0,   0.0   ← ★ 奇异点：不做 IK，只让 J6 转 ±180°
    P5  =    0.0, -775.0, 300.0,  90.0, 0.0,   0.0
    P6  =    0.0, -770.0, 300.0, 180.0, 0.0,   0.0
    P7  =  100.0, -770.0, 300.0, 180.0, 0.0,   0.0
    P8  =  100.0, -770.0, 300.0, 180.0, 0.0, 180.0   ← ★ 奇异点：不做 IK，只让 J6 转 ±180°
    P9  =    0.0, -770.0, 300.0, 180.0, 0.0, 180.0
    P10 = -500.0,    0.0, 300.0, 180.0, 0.0,   0.0
起点 = 原点（关节 0,0,0,0,0,0；按习惯机械臂开跑前就在原点）。

【★ P4 特殊处理（照抄 机械臂法兰真实运动.py 的“末端特异点/直接控制关节运动”选项）】
    该点的位姿在腕部奇异处，TCP 逆解会退化 ⇒ **不做 TCP 运动、不做 SolveIK**：
      · 取【当前实际关节】原样，只把 J6 加上 P4_J6_DELTA（默认 +180°）
      · 角度规范化到 (-180, 180]（照抄参考脚本第 512-514 行）
      · 仍然做一次碰撞预检（关节目标 ⇒ 无解可换，只测这一条）
      · 然后直接 MoveJ(关节目标) —— 即“直接控制关节运动”

【十段运动 & 延时】① 原点->P1  ② P1->P2  ③ P2->P3  ④ P3->P4(仅 J6 ±180°)  ⑤ P4->P5
                    ⑥ P5->P6   ⑦ P6->P7  ⑧ P7->P8(仅 J6 ±180°)  ⑨ P8->P9  ⑩ P9->P10 ；
                    ★ 每段运动之前额外延时 SEG_DELAY=2 秒。

【★ 碰撞预检（照抄 机械臂TCP仿真.py）】
    障碍物只取两个：
        安装台_650x650x80mm   —— 台面
        地面_禁止穿越          —— 地面
    ✗ 不管磨砂圆盘      ✗ 不考虑末端工具（参考脚本里“工具 × 障碍物”那段按要求省略）

    ★★ 关键：不拒绝任务，而是【换解】——
       robot.SolveIK_All(target) 枚举全部逆解
         ⇒ 每个解归一化到 ±180°，J6 再试 0 / −1 / +1 圈，滤掉超关节限位的
         ⇒ 按 _obstacle_posture_key 排序（肘部相对台面越高越优先）
         ⇒ 逐个 robot.MoveJ_Test(起点, 候选, minstep=1°)（碰撞检查已开）
         ⇒ 取【第一个通过】的候选作为本段的执行目标 ✓✓
       ⇒ 于是"预检通过的构型" 就是 "实际执行的构型"，且能绕开台面/地面继续运动。

【单步逻辑】严格照抄 机械臂法兰真实运动.py 的 execute_joint_target：
    ensure_connected() -> RDK.setRunMode(RUNMODE_RUN_ROBOT) -> robot.setSpeed(...) -> robot.MoveJ(target)
    ✗ 不开 30004   ✗ 不用 robot.Joints()/Busy()/setPoseFrame/setPoseTool
★ StoppedError 兜底仍保留（驱动会假报 'Robot not connected'，本环境常态）。

★ 运行前提：机械臂在原点；路径清空；手放急停上；RoboDK 已打开并加载【含台子和地面】的工作站。
"""
from robodk.robolink import *
from robodk.robomath import *
import tkinter as tk
from tkinter import scrolledtext
import math
import queue
import threading
import time

ROBOT_SPEED = 20.0       # ★ 速度：2026-09-28 按要求恢复到 20.0（此前减半为 10.0）
SEG_DELAY = 0.5          # ★ 每段运动前的延时（秒）：2026-09-28 按要求 2.0 → 0.5
NL = chr(10)

# ---- ★ 碰撞预检（只查台面 + 地面）----
COLLISION_OBSTACLES = ('安装台_650x650x80mm', '地面_禁止穿越')
TABLE_NAME = '安装台_650x650x80mm'
CHECK_MINSTEP_DEG = 1.0   # 与参考脚本的主检测粒度一致
CHECK_ENABLED = True      # 默认开启；GUI 可切换
MAX_CANDIDATES_TRY = 24   # 最多试多少个候选解（防御性上限）

# ---- 起点（关节；机械臂开跑前就在原点）----
ORIGIN_JOINTS = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

# ---- 两个目标点：轨迹3 的第 1、2 点，TCP（法兰 Fanuc）原样照抄 ----
P1_TCP = [500.0, 0.0, 300.0, 180.0, 0.0, 0.0]
P2_TCP = [0.0, -775.0, 300.0, -90.0, 0.0, 180.0]
P3_TCP = [100.0, -775.0, 300.0, -90.0, 0.0, 180.0]   # ★ 新增第 3 点（本次要求）
# ★★ 第 4 点 = 【奇异点】：不要走 TCP 运动（其 IK 在腕部奇异处会退化）
#    照抄 机械臂法兰真实运动.py 的"末端特异点"处理：完全跳过 SolveIK，
#    保持 J1~J5 不变，执行时只让 J6 转 ±180°（默认 +180°）。
P4_TCP = [100.0, -775.0, 300.0, -90.0, 0.0, 0.0]     # 仅作记录/日志，不用于 IK
P4_IS_SINGULAR = True
P4_J6_DELTA = 180.0                                  # ±180（+180 = 参考脚本默认）
# ★ 第 5 点：普通 TCP 点（回到正常 TCP 运动 + 碰撞预检换解）
P5_TCP = [0.0, -775.0, 300.0, 90.0, 0.0, 0.0]
# ★ 第 6 点：普通 TCP 点
P6_TCP = [0.0, -770.0, 300.0, 180.0, 0.0, 0.0]
# ★ 第 7 点：普通 TCP 点
P7_TCP = [100.0, -770.0, 300.0, 180.0, 0.0, 0.0]
# ★★ 第 8 点 = 【奇异点】（与第 4 点同类）：只差 Rz 0→180 ⇒ 直接控制关节，仅让 J6 转 ±180°
P8_TCP = [100.0, -770.0, 300.0, 180.0, 0.0, 180.0]   # 仅作记录/日志，不用于 IK
P8_IS_SINGULAR = True
P8_J6_DELTA = 180.0                                  # ±180（+180 = 参考脚本默认）
# ★ 第 9 / 10 点：普通 TCP 点
P9_TCP = [0.0, -770.0, 300.0, 180.0, 0.0, 180.0]
P10_TCP = [-500.0, 0.0, 300.0, 180.0, 0.0, 0.0]

# ---- 碰撞预检结果缓存（生命周期 = 单次预检；每次 _enable_obstacle_checks 清空）----
_plan_cache = {}

RDK = None
robot = None
text_log = None
run_btn = None
status_var = None
check_var = None
_running = False
_connected = False
_msg_q = queue.Queue()


def log(s):
    print(s, flush=True)
    _msg_q.put(str(s))


def _pump():
    try:
        while True:
            s = _msg_q.get_nowait()
            if text_log is not None:
                text_log.insert(tk.END, s + NL)
                text_log.see(tk.END)
    except queue.Empty:
        pass
    root.after(80, _pump)


# ============================================================
# 连接（照抄法兰脚本 ensure_connected）
# ============================================================
def init_robot():
    global RDK, robot
    if RDK is None:
        RDK = Robolink()
    if robot is None:
        robot = RDK.Item('', ITEM_TYPE_ROBOT)
    return robot is not None and robot.Valid()


def ensure_connected():
    global _connected
    if _connected:
        return True
    if not init_robot():
        log("!! 未在 RoboDK 站点里找到机器人（ITEM_TYPE_ROBOT）")
        return False
    try:
        robot.Connect()
        time.sleep(1.5)
        status, msg = robot.ConnectedState()
        log("连接状态: %s, %s" % (status, msg))
        if status != ROBOTCOM_READY:
            log("机器人未就绪：status=%s msg=%s" % (status, msg))
            _connected = False
            return False
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        log("RunMode: %s" % RDK.RunMode())
        _connected = True
        return True
    except Exception as e:  # noqa: BLE001
        log("连接失败: %s: %s" % (type(e).__name__, e))
        return False


# ============================================================
# 坐标换算（照抄法兰脚本的数学，一字不改）
# ============================================================
def _tool_mat():
    try:
        t = robot.PoseTool()
        return t if t is not None else eye(4)
    except Exception:
        return eye(4)


def fanuc_to_pose(x, y, z, rx, ry, rz):
    """【法兰】位姿(Fanuc) -> 当前工具下的 TCP 位姿（参考坐标系中）。"""
    return Fanuc_2_Pose([x, y, z, rx, ry, rz]) * _tool_mat()


def _sim_joints():
    q = list(robot.SimulatorJoints())
    return [float(v) for v in q[:6]] if len(q) >= 6 else None


def _fmt(vals):
    return ('X=%+.3f Y=%+.3f Z=%+.3f Rx=%+.3f Ry=%+.3f Rz=%+.3f'
            % (vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]))


def _fmtq(q):
    return ("J1=%+.4f J2=%+.4f J3=%+.4f J4=%+.4f J5=%+.4f J6=%+.4f" % tuple(list(q)[:6]))


def read_current():
    if not ensure_connected():
        return
    try:
        q = _sim_joints()
        log("当前位置（SimulatorJoints）：" + (_fmtq(q) if q else '(读不到 6 个值)'))
    except Exception as e:  # noqa: BLE001
        log("读取失败: %s: %s" % (type(e).__name__, e))


# ============================================================
# ★ 碰撞预检（台面 + 地面）—— 照抄 机械臂TCP仿真.py 的换解逻辑
# ============================================================
def _cache_key_joints(q):
    return tuple(round(float(v), 3) for v in q[:6])


def _movej_test_cached(start, end, minstep_deg):
    """robot.MoveJ_Test 的缓存包装（照抄参考脚本）。"""
    key = ('movej_test', _cache_key_joints(start), _cache_key_joints(end),
           round(float(minstep_deg), 6))
    if key not in _plan_cache:
        _plan_cache[key] = robot.MoveJ_Test(start, end, minstep_deg=minstep_deg)
    elif _plan_cache[key] == 0:
        robot.setJoints(list(end[:6]))
    return _plan_cache[key]


def _collision_details():
    pairs = RDK.CollisionPairs()
    return '；'.join('%s[连杆%d] 与 %s[连杆%d]' % (a.Name(), ia, b.Name(), ib)
                     for a, b, ia, ib in pairs) or '路径碰撞或关节不可行'


def _enable_obstacle_checks():
    """照抄参考脚本，但按要求【不给末端工具配碰撞对】。
       必须在 RUNMODE_SIMULATE 下调用。"""
    if RDK.RunMode() != RUNMODE_SIMULATE:
        raise RuntimeError('障碍物碰撞预检仅允许在仿真模式执行。')
    _plan_cache.clear()
    for name in COLLISION_OBSTACLES:
        obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
        if not obstacle.Valid():
            raise RuntimeError('缺少障碍物模型：%s，请加载包含台子和地面的工作站。' % name)
        if name == TABLE_NAME:
            # 固定底座与台面本来就接触，不参与判定（照抄参考脚本）
            if RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0) != 1:
                raise RuntimeError('无法配置安装台与固定底座的接触关系。')
        for link in range(1, 7):
            if RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0) != 1:
                raise RuntimeError('无法启用 %s 与连杆%d 的碰撞检查。' % (name, link))
        # ★ 参考脚本这里还有 “for tool in RDK.ItemList(ITEM_TYPE_TOOL)”
        #   —— 本次按要求【不考虑末端工具】，故省略。
    RDK.setCollisionActive(COLLISION_ON)


def _obstacle_posture_key(q, reference=None):
    """照抄参考脚本：优先"肘部（连杆3）离台面更高"的构型；再优先离当前关节更近的。"""
    height = 0.0
    try:
        table = RDK.Item(TABLE_NAME, ITEM_TYPE_OBJECT)
        if table.Valid():
            elbow = invH(table.PoseAbs()) * robot.PoseAbs() * robot.JointPoses(q)[3]
            height = float(elbow.Pos()[2])
    except Exception:
        height = 0.0
    ref = reference or [0.0] * 6
    return (-round(height, 6), sum((v - r) ** 2 for v, r in zip(q, ref)), tuple(q))


def _tcp_target_to_flange(pose):
    """TCP 位姿 -> 法兰位姿（照抄参考脚本 机械臂TCP仿真.py 第 758-760 行）。
    ★ 必须做这一步：SolveIK / SolveIK_All 要的是【法兰】位姿，而 fanuc_to_pose
      返回的是【TCP】位姿（已乘过工具矩阵）。漏掉这一步会解不出逆解。"""
    return robot.PoseFrame() * pose * invH(robot.PoseTool())


def _singular_j6_target(start_joints, delta):
    """构造"末端特异点"的关节目标：保持 J1~J5 不变，只让 J6 转 ±delta。

    照抄参考脚本 机械臂法兰真实运动.py 的“末端特异点/直接控制关节运动”做法：
      · 完全跳过 SolveIK（该位姿在腕部奇异处，逆解会退化）
      · J6 加 ±delta（默认 ±180°）
      · 角度规范化到 (-180, 180]（参考脚本第 512-514 行）
    """
    q = [float(v) for v in start_joints[:6]]
    q[5] += delta
    q = [((v + 180.0) % 360.0) - 180.0 for v in q]
    return [180.0 if v <= -180.0 else v for v in q]


def _run_singular_segment(tag, p_label, delta, tcp_for_log, seg_index, seg_total, fallback_start=None):
    """执行一个"末端特异点"段：跳过 IK，仅 J6 ±delta，仍然做碰撞预检。

    返回 (是否放行, 起点关节, 目标关节)。
    """
    log("")
    log("--- 段 %d / %d：%s（奇异点：跳过 IK，仅 J6 %+g°）---" % (seg_index, seg_total, tag, delta))
    log("    %s  目标（仅记录）%s" % (p_label, _fmt(tcp_for_log)))
    log("    ★ 该点标记为末端特异点 ⇒ 不做 TCP 逆解；保持 J1~J5 不变，只让 J6 转 %+g°" % delta)
    log("      （做法照抄 机械臂法兰真实运动.py 的“末端特异点/直接控制关节运动”选项）")
    log("延时 %.1f 秒 ..." % SEG_DELAY)
    time.sleep(SEG_DELAY)

    start = _sim_joints() or fallback_start or list(ORIGIN_JOINTS)
    target = _singular_j6_target(start, delta)
    log("      起点关节：%s" % _fmtq(start))
    log("      目标关节：%s   （J6 %+.4f° → %+.4f°）" % (_fmtq(target), start[5], target[5]))

    allow, chosen = _do_segment_check(start, target, "段%d %s（仅 J6 %+g°）" % (seg_index, tag, delta))
    return allow, start, (chosen if chosen else target)


def _ik_candidates(pose, reference):
    """枚举目标位姿的全部可用关节解（照抄参考脚本 _trajectory_start_candidates）。"""
    try:
        solutions = robot.SolveIK_All(_tcp_target_to_flange(pose))   # ★ 法兰位姿
    except Exception as e:  # noqa: BLE001
        log("      SolveIK_All 异常：%s: %s" % (type(e).__name__, e))
        return []
    try:
        lower, upper, _ = robot.JointLimits()
        lower = [float(v) for v in list(lower)[:6]]
        upper = [float(v) for v in list(upper)[:6]]
    except Exception:
        lower = [-360.0] * 6
        upper = [360.0] * 6

    candidates = []
    for solution in solutions:
        q = [((float(v) + 180.0) % 360.0) - 180.0 for v in list(solution)[:6]]
        if len(q) != 6:
            continue
        for turns6 in (0, -1, 1):
            cand = q[:]
            cand[5] += 360.0 * turns6
            if all(lower[j] <= cand[j] <= upper[j] for j in range(6)):
                if not any(max(abs(a - b) for a, b in zip(cand, old)) < 1e-6 for old in candidates):
                    candidates.append(cand)
    # 同一姿态保留"接近当前圈数"的表示（照抄参考脚本）
    for q in candidates[:]:
        try:
            nearest = [min((v + 360 * k for k in range(
                int(math.ceil((lower[j] - v) / 360.0)),
                int(math.floor((upper[j] - v) / 360.0)) + 1)),
                key=lambda a: abs(a - reference[j]))
                for j, v in enumerate(q)]
        except Exception:
            continue
        if not any(max(abs(a - b) for a, b in zip(nearest, old)) < 1e-6 for old in candidates):
            candidates.append(nearest)
    return sorted(candidates, key=lambda q: _obstacle_posture_key(q, reference))


def _check_segment(start_joints, target, tag):
    """在【仿真模式】下为 start_joints -> target 这一段【挑一个不撞台面/地面的构型】。

    target 可以是关节列表（6 个数，此时无解可换）或位姿（Mat，此时枚举全部逆解换解）。
    返回 (ok, chosen_joints, message)。
    ★ 无论成败都把 RunMode 恢复原值；只动模型，不发真机指令。
    """
    saved_mode = RDK.RunMode()
    saved_joints = None
    try:
        RDK.setRunMode(RUNMODE_SIMULATE)
        _enable_obstacle_checks()
        try:
            saved_joints = [float(v) for v in robot.Joints()][:6]
        except Exception:
            saved_joints = None

        # ---- 目标是关节（如"回原点"）：没有候选可换，只测这一条 ----
        if isinstance(target, (list, tuple)) and len(target) == 6:
            robot.setJoints(list(start_joints[:6]))
            status = _movej_test_cached(start_joints, list(target), CHECK_MINSTEP_DEG)
            if status == 0:
                return True, list(target), '通过（关节目标，status=0）'
            return False, None, '不通过（status=%s）：%s' % (status, _collision_details())

        # ---- 目标是位姿：枚举全部逆解，按肘高排序，逐个测 ----
        cands = _ik_candidates(target, start_joints)
        log("      逆解候选 %d 个（SolveIK_All，已转法兰位姿），按【肘部离台面高度】排序后逐个做 MoveJ_Test …" % len(cands))
        if not cands:
            # ★ 兜底：让 RoboDK 自己解（MoveJ_Test 也接受位姿）——TCP 位姿 / 法兰位姿各试一次
            log("      枚举为空 ⇒ 兜底：直接让 RoboDK 自己解（MoveJ_Test 接受位姿）")
            for label, tgt in (('TCP 位姿', target), ('法兰位姿', _tcp_target_to_flange(target))):
                try:
                    robot.setJoints(list(start_joints[:6]))
                    st = robot.MoveJ_Test(start_joints, tgt, minstep_deg=CHECK_MINSTEP_DEG)
                except Exception as e:  # noqa: BLE001
                    log("      %s 兜底异常：%s: %s" % (label, type(e).__name__, e))
                    continue
                if st == 0:
                    try:
                        end = [float(v) for v in robot.Joints()][:6]
                    except Exception:
                        end = None
                    log("      ✓ %s 兜底通过（status=0），终点关节 %s"
                        % (label, _fmtq(end) if end else '(读不到)'))
                    return True, end, '通过（%s 兜底，RoboDK 自解，status=0）' % label
                log("      ✗ %s 兜底未通过 status=%s" % (label, st))
            return False, None, '没有可用逆解（SolveIK_All 无解，且两种位姿兜底都未通过）'

        tried = 0
        for cand in cands[:MAX_CANDIDATES_TRY]:
            tried += 1
            try:
                robot.setJoints(list(start_joints[:6]))
            except Exception:
                pass
            status = _movej_test_cached(start_joints, cand, CHECK_MINSTEP_DEG)
            h = _obstacle_posture_key(cand, start_joints)[0]
            if status == 0:
                log("      ✓ 第 %d 个候选通过（肘部相对台面 %.1f mm）：%s" % (tried, -h, _fmtq(cand)))
                return True, cand, '通过（第 %d/%d 个候选，status=0）' % (tried, len(cands))
            log("      ✗ 第 %d 个候选未通过 status=%s（肘部 %.1f mm）" % (tried, status, -h))
        return False, None, '全部 %d 个候选都未通过：%s' % (tried, _collision_details())
    except Exception as e:  # noqa: BLE001
        return False, None, '预检异常：%s: %s' % (type(e).__name__, e)
    finally:
        try:
            if saved_joints is not None:
                robot.setJoints(saved_joints)     # 只影响模型
        except Exception:
            pass
        try:
            RDK.setRunMode(saved_mode)            # ★ 必须切回原模式
        except Exception:
            pass


# ============================================================
# 单步运动（照抄 execute_joint_target，并保留你自己的 StoppedError 兜底）
# ============================================================
def _stationary(a, b, tol=0.05):
    return bool(a) and bool(b) and max(abs(x - y) for x, y in zip(a, b)) <= tol


def _move_one(target, tag, target_joints=None):
    """单步 MoveJ。

    照抄 execute_joint_target 的四步；但**保留** 机械臂TCP真实运动.py 第 618-632 行的兜底：
    驱动会假报 `StoppedError: Robot not connected`（指令其实已发出，报错发生在"等待完成"阶段），
    此环境里是常态，不能当失败。
    判据改用【RoboDK 模型关节 SimulatorJoints】（连接真机时模型与真机同步）
    —— 不读 30004、不碰任何端口，因此不会再被端口占用拖死。
      ① 若给了 target_joints（原点那种）：模型到位即算完成；
      ② 否则要求"确实动过 + 已停稳"：证明指令执行过且这一段落停住了。
    """
    q_before = _sim_joints()
    log("  发送 MoveJ -> %s" % tag)
    RDK.setRunMode(RUNMODE_RUN_ROBOT)
    robot.setSpeed(ROBOT_SPEED)
    try:
        robot.MoveJ(target)                      # ← 照抄：不加兜底、不读反馈
        log("  ✓ %s：MoveJ 命令已发送并返回" % tag)
        return True
    except StoppedError as exc:
        if str(exc).strip() != 'Robot not connected':
            raise                                # 其它 StoppedError 一律照抄原样上抛
    log("  ⚠ 驱动返回 'Robot not connected'（已知假报警；发生在等待完成阶段）")
    log("     判定中：用模型关节（SimulatorJoints）确认这一段是否真的走完 …")
    for attempt in range(10):
        time.sleep(0.3)
        a = _sim_joints()
        time.sleep(0.3)
        b = _sim_joints()
        if not _stationary(a, b):
            continue                             # 还在动，继续等
        if target_joints is not None:
            if max(abs(x - y) for x, y in zip(b, target_joints)) <= 0.5:
                log("  ✓ %s：模型关节已到目标且停稳 %s ⇒ 计为完成，不重发" % (tag, _fmtq(b)))
                return True
        elif q_before is not None and max(abs(x - y) for x, y in zip(b, q_before)) > 0.05:
            log("  ✓ %s：已停稳且确实动过（%s → %s）⇒ 计为完成，不重发"
                % (tag, _fmtq(q_before), _fmtq(b)))
            return True
    raise RuntimeError("驱动报 'Robot not connected'，但模型关节既未到位也未显示『动过且停稳』"
                       "（第 %d 次尝试后）⇒ 判定为真失败" % (10 + 1))


def _do_segment_check(start_joints, target, tag):
    """执行一段前的碰撞预检（含换解）；返回 (是否放行, 本段要执行的关节目标)。"""
    if not CHECK_ENABLED:
        log("  （碰撞预检已关闭，跳过）")
        return True, (list(target) if isinstance(target, (list, tuple)) and len(target) == 6 else None)
    log("  碰撞预检（台面 + 地面，含换解）：%s" % tag)
    ok, chosen, msg = _check_segment(start_joints, target, tag)
    if ok:
        log("  ✓ %s：预检通过 —— %s" % (tag, msg))
        return True, chosen
    log("  ✗ %s：预检未通过 ⇒ 本段不执行，以避免碰撞" % tag)
    log("     原因：%s" % msg)
    return False, None


def _worker():
    global _running
    try:
        log("")
        log("=" * 64)
        log("单步测试（TCP 坐标版 + 台面/地面碰撞预检/换解）：原点 -> 轨迹3 P1 -> 轨迹3 P2")
        log("速度 %.1f ｜ 每段运动前延时 %.1f 秒 ｜ 碰撞预检 %s"
            % (ROBOT_SPEED, SEG_DELAY, "开" if CHECK_ENABLED else "关"))
        log("障碍物：%s（不含磨砂圆盘；不含末端工具）" % ', '.join(COLLISION_OBSTACLES))
        log("=" * 64)
        if not ensure_connected():
            raise RuntimeError("连接未建立，取消")

        try:
            q0 = _sim_joints()
            if q0:
                log("起始位置（SimulatorJoints）：" + _fmtq(q0))
                log("距离原点最大偏差 = %.4f°" % max(abs(v) for v in q0))
        except Exception as e:  # noqa: BLE001
            log("读取起始位置失败（不阻断）：%s: %s" % (type(e).__name__, e))

        origin = list(ORIGIN_JOINTS)   # ★ 原点是【关节】目标（不是位姿！）
        p1 = fanuc_to_pose(*P1_TCP)
        p2 = fanuc_to_pose(*P2_TCP)
        p3 = fanuc_to_pose(*P3_TCP)
        p5 = fanuc_to_pose(*P5_TCP)
        p6 = fanuc_to_pose(*P6_TCP)
        p7 = fanuc_to_pose(*P7_TCP)
        p9 = fanuc_to_pose(*P9_TCP)
        p10 = fanuc_to_pose(*P10_TCP)

        # ---- 段 1 / 10：当前位置 -> 原点 -> P1 ----
        log("")
        log("--- 段 1 / 10：原点 -> P1 ---")
        log("    原点目标（关节）%s" % _fmtq(ORIGIN_JOINTS))
        log("    P1  目标 %s" % _fmt(P1_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        # ★ 碰撞预检：回到原点这一段（关节目标，无解可换）
        seg_start = _sim_joints() or list(ORIGIN_JOINTS)
        allow0, chosen0 = _do_segment_check(seg_start, origin, "段1a 当前 -> 原点")
        if not allow0:
            log("")
            log("!! 回到原点这一段预检未通过 ⇒ 取消（未发送任何运动指令）")
            raise RuntimeError("段1a（回原点）碰撞预检未通过")
        _move_one(origin, "原点", ORIGIN_JOINTS)

        # ★ 碰撞预检：原点 -> P1（位姿目标 ⇒ 会枚举逆解并换解）
        seg_start = _sim_joints() or list(ORIGIN_JOINTS)
        allow1, chosen1 = _do_segment_check(seg_start, p1, "段1b 原点 -> P1")
        if not allow1:
            log("")
            log("!! 段1 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段1 碰撞预检未通过")
        # ★ 执行【预检选中的那个构型】，保证"检查过的解 = 走的解"
        _move_one(chosen1 if chosen1 else p1, "P1（轨迹3 第1点）", chosen1)

        # ---- 段 2 / 10：P1 -> P2 ----
        log("")
        log("--- 段 2 / 10：P1 -> P2 ---")
        log("    P2  目标 %s" % _fmt(P2_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start2 = _sim_joints() or chosen1 or list(ORIGIN_JOINTS)
        allow2, chosen2 = _do_segment_check(seg_start2, p2, "段2 P1 -> P2")
        if not allow2:
            log("")
            log("!! 段2 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段2 碰撞预检未通过")
        _move_one(chosen2 if chosen2 else p2, "P2（轨迹3 第2点）", chosen2)

        # ---- 段 3 / 10：P2 -> P3 ----
        log("")
        log("--- 段 3 / 10：P2 -> P3 ---")
        log("    P3  目标 %s" % _fmt(P3_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start3 = _sim_joints() or chosen2 or list(ORIGIN_JOINTS)
        allow3, chosen3 = _do_segment_check(seg_start3, p3, "段3 P2 -> P3")
        if not allow3:
            log("")
            log("!! 段3 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段3 碰撞预检未通过")
        _move_one(chosen3 if chosen3 else p3, "P3（第3点）", chosen3)

        # ---- 段 4 / 10：P3 -> P4（★ 奇异点：不走 TCP 运动，直接控制关节 —— 只让 J6 转 ±180°）----
        allow4, seg_start4, j6_target = _run_singular_segment(
            "P3 -> P4", "P4", P4_J6_DELTA, P4_TCP, 4, 8, fallback_start=chosen3)
        if not allow4:
            log("")
            log("!! 段4 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段4 碰撞预检未通过")
        _move_one(j6_target, "P4（第4点，仅 J6 %+g°）" % P4_J6_DELTA, j6_target)

        # ---- 段 5 / 10：P4 -> P5（普通 TCP 点 ⇒ 回到 TCP 运动 + 碰撞预检换解）----
        log("")
        log("--- 段 5 / 10：P4 -> P5 ---")
        log("    P5  目标 %s" % _fmt(P5_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start5 = _sim_joints() or chosen4 or j6_target or list(ORIGIN_JOINTS)
        allow5, chosen5 = _do_segment_check(seg_start5, p5, "段5 P4 -> P5")
        if not allow5:
            log("")
            log("!! 段5 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段5 碰撞预检未通过")
        _move_one(chosen5 if chosen5 else p5, "P5（第5点）", chosen5)

        # ---- 段 6 / 10：P5 -> P6（普通 TCP 点）----
        log("")
        log("--- 段 6 / 10：P5 -> P6 ---")
        log("    P6  目标 %s" % _fmt(P6_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start6 = _sim_joints() or chosen5 or list(ORIGIN_JOINTS)
        allow6, chosen6 = _do_segment_check(seg_start6, p6, "段6 P5 -> P6")
        if not allow6:
            log("")
            log("!! 段6 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段6 碰撞预检未通过")
        _move_one(chosen6 if chosen6 else p6, "P6（第6点）", chosen6)

        # ---- 段 7 / 10：P6 -> P7（普通 TCP 点）----
        log("")
        log("--- 段 7 / 10：P6 -> P7 ---")
        log("    P7  目标 %s" % _fmt(P7_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start7 = _sim_joints() or chosen6 or list(ORIGIN_JOINTS)
        allow7, chosen7 = _do_segment_check(seg_start7, p7, "段7 P6 -> P7")
        if not allow7:
            log("")
            log("!! 段7 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段7 碰撞预检未通过")
        _move_one(chosen7 if chosen7 else p7, "P7（第7点）", chosen7)

        # ---- 段 8 / 10：P7 -> P8（★ 奇异点：不走 TCP 运动，直接控制关节 —— 只让 J6 转 ±180°）----
        allow8, seg_start8, j6_target8 = _run_singular_segment(
            "P7 -> P8", "P8", P8_J6_DELTA, P8_TCP, 8, 8, fallback_start=chosen7)
        if not allow8:
            log("")
            log("!! 段8 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段8 碰撞预检未通过")
        _move_one(j6_target8, "P8（第8点，仅 J6 %+g°）" % P8_J6_DELTA, j6_target8)

        # ---- 段 9 / 10：P8 -> P9（普通 TCP 点）----
        log("")
        log("--- 段 9 / 10：P8 -> P9 ---")
        log("    P9  目标 %s" % _fmt(P9_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start9 = _sim_joints() or j6_target8 or list(ORIGIN_JOINTS)
        allow9, chosen9 = _do_segment_check(seg_start9, p9, "段9 P8 -> P9")
        if not allow9:
            log("")
            log("!! 段9 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段9 碰撞预检未通过")
        _move_one(chosen9 if chosen9 else p9, "P9（第9点）", chosen9)

        # ---- 段 10 / 10：P9 -> P10（普通 TCP 点）----
        log("")
        log("--- 段 10 / 10：P9 -> P10 ---")
        log("    P10 目标 %s" % _fmt(P10_TCP))
        log("延时 %.1f 秒 ..." % SEG_DELAY)
        time.sleep(SEG_DELAY)

        seg_start10 = _sim_joints() or chosen9 or list(ORIGIN_JOINTS)
        allow10, chosen10 = _do_segment_check(seg_start10, p10, "段10 P9 -> P10")
        if not allow10:
            log("")
            log("!! 段10 因碰撞预检未通过而取消（未发送任何运动指令）")
            raise RuntimeError("段10 碰撞预检未通过")
        _move_one(chosen10 if chosen10 else p10, "P10（第10点）", chosen10)

        log("")
        log("=" * 64)
        try:
            q = _sim_joints()
            if q:
                log("结束位置（SimulatorJoints）：" + _fmtq(q))
        except Exception:
            pass
        log("全部完成 ✓")
        log("=" * 64)
    except Exception as e:  # noqa: BLE001
        import traceback
        log("")
        log("!! 中断：%s: %s" % (type(e).__name__, e))
        for line in traceback.format_exc().rstrip().splitlines():
            log("   " + line)
        log("（照抄原脚本行为：不自动重发运动；请检查机械臂与报警）")
    finally:
        _running = False
        try:
            RDK.setRunMode(RUNMODE_RUN_ROBOT)     # 收尾确保回到真机模式
        except Exception:
            pass
        try:
            run_btn.configure(state=tk.NORMAL, text="启动运动")
            status_var.set("就绪")
        except Exception:
            pass


def start_motion():
    global _running, CHECK_ENABLED
    if _running:
        log("已在运行中，忽略本次点击")
        return
    try:
        CHECK_ENABLED = bool(check_var.get())
    except Exception:
        pass
    _running = True
    run_btn.configure(state=tk.DISABLED, text="运行中 ...")
    status_var.set("运行中")
    log("")
    log("########## 启动运动 ##########")
    threading.Thread(target=_worker, daemon=True).start()


# ============================================================
# GUI
# ============================================================
root = tk.Tk()
root.title("RoboDK - 原点→P1→P2→P3→P4(奇异点)→P5→P6→P7→P8(奇异点)→P9→P10 单步测试")
root.geometry("1060x740")
root.resizable(True, True)

frame_top = tk.LabelFrame(root, text="测试内容（单步 / TCP 坐标 / 台面+地面碰撞预检，含自动换解）")
frame_top.pack(fill=tk.X, padx=10, pady=6)
tk.Label(frame_top, anchor=tk.W, justify=tk.LEFT,
         text=("段1:原点->P1  段2:P1->P2  段3:P2->P3  段4:P3->P4(仅J6±180°)  段5:P4->P5  段6:P5->P6  段7:P6->P7  段8:P7->P8(仅J6±180°)  段9:P8->P9  段10:P9->P10" + NL
               + "        每段运动前延时 " + str(SEG_DELAY) + " 秒" + NL
               + "P1（轨迹3 第1点）= 500.0, 0.0, 300.0, 180.0, 0.0, 0.0              （TCP / 法兰 Fanuc）" + NL
               + "P2（轨迹3 第2点）= 0.0, -775.0, 300.0, -90.0, 0.0, 180.0" + NL
               + "P3（第3点）      = 100.0, -775.0, 300.0, -90.0, 0.0, 180.0" + NL
               + "P4（★奇异点）    = 100.0, -775.0, 300.0, -90.0, 0.0, 0.0   ← 不做 TCP 逆解" + NL
               + "P5（第5点）      = 0.0, -775.0, 300.0, 90.0, 0.0, 0.0      ← 普通 TCP 点" + NL
               + "P6（第6点）      = 0.0, -770.0, 300.0, 180.0, 0.0, 0.0     ← 普通 TCP 点" + NL
               + "P7（第7点）      = 100.0, -770.0, 300.0, 180.0, 0.0, 0.0   ← 普通 TCP 点" + NL
               + "P8（★奇异点）    = 100.0, -770.0, 300.0, 180.0, 0.0, 180.0 ← 不做 TCP 逆解" + NL
               + "P9（第9点）      = 0.0, -770.0, 300.0, 180.0, 0.0, 180.0   ← 普通 TCP 点" + NL
               + "P10（第10点）    = -500.0, 0.0, 300.0, 180.0, 0.0, 0.0     ← 普通 TCP 点" + NL
               + "   ★ P4 / P8 走“直接控制关节运动”：保持 J1~J5 不变，只让 J6 转 " + str(P4_J6_DELTA)
               + "°，然后直接 MoveJ(关节)" + NL
               + "★ 碰撞预检：障碍物 = 安装台_650x650x80mm（台面）+ 地面_禁止穿越（地面）" + NL
               + "   做法照抄 机械臂TCP仿真.py：SolveIK_All 枚举全部逆解 → 按“肘部离台面高度”排序" + NL
               + "   → 逐个 MoveJ_Test（1° 粒度、碰撞开）→ 取第一个通过的构型去执行 ✓"),
         font=("Microsoft YaHei", 10)).pack(fill=tk.X, padx=8, pady=4)

frame_btn = tk.LabelFrame(root, text="操作")
frame_btn.pack(fill=tk.X, padx=10, pady=6)
run_btn = tk.Button(frame_btn, text="启动运动", width=18, bg="#4CAF50", fg="white",
                    font=("Microsoft YaHei", 11, "bold"), command=start_motion)
run_btn.pack(side=tk.LEFT, padx=8, pady=8)
check_var = tk.BooleanVar(value=True)
tk.Checkbutton(frame_btn, text="碰撞预检（台面+地面，含换解）", variable=check_var,
               font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=6, pady=8)
tk.Button(frame_btn, text="读取当前位置", width=16, font=("Microsoft YaHei", 10),
          command=lambda: threading.Thread(target=read_current, daemon=True).start()
          ).pack(side=tk.LEFT, padx=6, pady=8)
tk.Button(frame_btn, text="清空日志", width=12, font=("Microsoft YaHei", 10),
          command=lambda: text_log.delete("1.0", tk.END)).pack(side=tk.LEFT, padx=6, pady=8)
status_var = tk.StringVar(value="就绪")
tk.Label(frame_btn, textvariable=status_var, anchor=tk.W, fg="#555",
         font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=16)

frame_log = tk.LabelFrame(root, text="日志")
frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
text_log = scrolledtext.ScrolledText(frame_log, font=("Consolas", 10), height=20)
text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

log("程序就绪。模式：RUNMODE_RUN_ROBOT + robot.Connect()；碰撞预检在 RUNMODE_SIMULATE 下进行")
log("测试 = 单步：原点 -> P1 -> P2 -> P3 -> P4(奇异点) -> P5 -> P6 -> P7 -> P8(奇异点) -> P9 -> P10（TCP 坐标）")
log("P1 = 500.0, 0.0, 300.0, 180.0, 0.0, 0.0")
log("P2 = 0.0, -775.0, 300.0, -90.0, 0.0, 180.0")
log("P3 = 100.0, -775.0, 300.0, -90.0, 0.0, 180.0")
log("P4 = 100.0, -775.0, 300.0, -90.0, 0.0, 0.0   ★奇异点：不做 IK，保持 J1~J5，只让 J6 转 %+g°" % P4_J6_DELTA)
log("P5 = 0.0, -775.0, 300.0, 90.0, 0.0, 0.0      （普通 TCP 点）")
log("P6 = 0.0, -770.0, 300.0, 180.0, 0.0, 0.0     （普通 TCP 点）")
log("P7 = 100.0, -770.0, 300.0, 180.0, 0.0, 0.0   （普通 TCP 点）")
log("P8 = 100.0, -770.0, 300.0, 180.0, 0.0, 180.0  ★奇异点：不做 IK，保持 J1~J5，只让 J6 转 %+g°" % P8_J6_DELTA)
log("P9 = 0.0, -770.0, 300.0, 180.0, 0.0, 180.0   （普通 TCP 点）")
log("P10 = -500.0, 0.0, 300.0, 180.0, 0.0, 0.0    （普通 TCP 点）")
log("★ 碰撞预检障碍物：安装台_650x650x80mm（台面）、地面_禁止穿越（地面）；不含磨砂圆盘、不含末端工具")
log("★ 预检不通过时会自动换解（SolveIK_All 全部逆解 → 肘高排序 → 逐个 MoveJ_Test）")
log("★ 运行前请确认：机械臂在原点、路径清空、手放急停上、工作站里已加载台子和地面")
log("")
_pump()
root.mainloop()
