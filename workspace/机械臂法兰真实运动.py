# -*- coding: utf-8 -*-
"""
RoboDK 实机运动控制 —— 【法兰坐标版】（不把末端工具算进去）
- 单点：法兰位姿(Fanuc 格式) 输入 -> IK 检测 -> MoveL/MoveJ 执行
- 连续轨迹：法兰位姿/关节点列表 -> 逐点 IK 检测 -> MoveJ+MoveL 序列
- 关节点直通：J1~J6 -> 实机 MoveJ（不经 TCP/IK，本来就是法兰无关）

坐标约定（与 机械臂TCP真实运动.py 的唯一区别）：
  本脚本输入/显示/记录的都是【法兰】(flange) 位姿 —— 不含末端工具。
  RoboDK 的 SolveIK / MoveL / MoveJ 一律按 TCP 解释位姿，所以：
    * 运动前：TCP目标 = 法兰 × 当前工具(PoseTool)   [fanuc_to_pose 里做]
    * 读取时：法兰   = invH(PoseFrame) × SolveFK(Joints)   [完全不含工具]
  ⇒ 换工具不需要改本脚本的任何坐标；工具只在最后一次换算里出现，且会在日志里打印。

⚠️ 与 TCP 版的数据不通用：TCP版导出的 JSON 里存的是 TCP 坐标，直接导入本脚本
   会整体偏移一个工具量。请只用本脚本自己导出的 JSON。

模式：RUNMODE_RUN_ROBOT + robot.Connect()
"""

from robodk.robolink import *
from robodk.robomath import *
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import time
import math
import json
import itertools

ROBOT_SPEED = 20.0
NL = chr(10)

# ============================================================
# 连续运动逻辑的常量与预检缓存（整段移植自仿真脚本，算法未改动）
# ============================================================
ALLOW_MOTION = True
MOVEJ_FALLBACK_MAX_DEVIATION_MM = 500.0  # MoveL失败后，MoveJ轨迹允许偏离TCP直线段的最大距离

# ============================================================
# 碰撞判断排除清单（本阶段：磨砂圆盘暂不参与碰撞判断）
# ============================================================
# 工位对象名只要【包含】下面任一关键字，就显式关掉它与机器人和所有工具的
# 碰撞判断（只关这一个对象的配对，安装台/地面等其它障碍物不受影响）。
# 当前命中的工位对象：磨砂圆柱_R180_H40（即磨砂圆盘）。
# 要恢复它的碰撞判断：把这里改成空元组 EXCLUDED_COLLISION_KEYWORDS = () 即可。
# 注意：RoboDK 默认就会对工位内对象做碰撞判断，所以这里是"显式关掉"，
# 而不是"不再添加"。
EXCLUDED_COLLISION_KEYWORDS = ('磨砂',)

# ============================================================
# 预检结果缓存（性能优化：分支重试不重复计算，判定结果不变）
# ============================================================
# 缓存生命周期 = 单次预检规划：_enable_obstacle_checks() 在每次进入预检时
# 清空缓存，因此障碍物/工作站状态的任何变化都会在下一次预检中即时生效。
_plan_cache = {}

def _cache_key_joints(q):
    return tuple(round(float(v), 3) for v in q[:6])

def _cache_key_pose(pose):
    return tuple(tuple(round(float(v), 6) for v in row) for row in pose.rows)

def _movej_test_cached(start, end, minstep_deg):
    """robot.MoveJ_Test 的缓存包装，返回值与直接调用完全一致。
    成功时与原调用一样把仿真关节停在终点；失败路径的规划器只依赖局部
    关节变量（不读取此时的模型关节状态），无需复现失败的副作用。"""
    key = ('movej_test', _cache_key_joints(start), _cache_key_joints(end),
           round(float(minstep_deg), 6))
    if key not in _plan_cache:
        _plan_cache[key] = robot.MoveJ_Test(start, end, minstep_deg=minstep_deg)
    elif _plan_cache[key] == 0:
        robot.setJoints(list(end[:6]))
    return _plan_cache[key]

RDK = Robolink()

def _tool_mat():
    """当前工具位姿（TCP 相对法兰）。取不到就退回单位阵（等价于以法兰为 TCP）。"""
    try:
        t = robot.PoseTool()
        return t if t is not None else eye(4)
    except Exception:
        return eye(4)

def fanuc_to_pose(x, y, z, rx, ry, rz):
    """【法兰】位姿(Fanuc) -> 当前工具下的 TCP 位姿。

    操作员给的是法兰坐标；RoboDK 的 SolveIK/MoveL/MoveJ 都要 TCP，
    所以在入口处做一次 法兰 × 工具，之后所有既有代码原样复用。
    """
    flange = Fanuc_2_Pose([x, y, z, rx, ry, rz])
    return flange * _tool_mat()

def pose_to_fanuc(pose):
    return Pose_2_Fanuc(pose)

def _joints6():
    """读取当前关节（6 个）。

    ⚠️ 本环境**不能用 robot.Joints()**：实机模式下它会去读真机驱动，超时后 RoboDK
    只返回 1×1 的 [[0]]（屏幕上是 "Robot connection failed timed out: Working..."），
    后面任何按 6 个用的地方都会 IndexError。已验证的实机脚本（机械臂TCP真实运动.py）
    一律用 SimulatorJoints()（RoboDK 模型姿态；连接真机时模型与真机同步）。
    读不到 6 个就明确报错，不再让 IndexError 冒到上层。
    """
    try:
        q = list(robot.SimulatorJoints())
    except Exception as exc:
        raise RuntimeError(f'读取当前关节失败：{type(exc).__name__}: {exc}')
    if len(q) < 6:
        raise RuntimeError(f'读取当前关节失败：SimulatorJoints 只返回 {len(q)} 个值 {q}；'
                           '请确认 RoboDK 里机器人已连接、模型姿态显示正常。')
    return [float(v) for v in q[:6]]


def current_flange_pose():
    """当前【法兰】位姿（当前参考坐标系下，不含工具）。

    等价于 invH(PoseFrame) × Pose，但不引入工具量，因此工具的改动不会影响读数。
    """
    return invH(robot.PoseFrame()) * robot.SolveFK(_joints6())

# ---- 名称适配：仿真脚本的连续运动逻辑使用下面两个名字 ----
# 这是零改动的转发（法兰边界仍然只在 _tool_mat / fanuc_to_pose / pose_to_fanuc /
# current_flange_pose 里实现，坐标数学一律没有改动）。
def fanuc_values_to_pose(x, y, z, rx, ry, rz):
    """等同 fanuc_to_pose：法兰位姿(Fanuc) -> 当前工具下的 TCP 位姿。"""
    return fanuc_to_pose(x, y, z, rx, ry, rz)

def pose_to_fanuc_values(pose):
    """等同 pose_to_fanuc：位姿 -> Fanuc 六数。"""
    return pose_to_fanuc(pose)

# ---- 获取机器人 ----
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise Exception("未找到机器人")

# ---- 全局变量 ----
text_points = None
text_log = None
record_text = None
entries_single = None
entries_joint = None
move_type = None
trajectory_records = []
_connected = False
simulation_running = False   # 连续运动是否正在运行（移植自仿真脚本）

# ============================================================
# 日志
# ============================================================
def log(s):
    """写三处：stdout + 单点日志(text_log) + 连续运动日志(traj_log_output/traj_status_var)。"""
    print(s)
    if text_log:
        try:
            text_log.insert(tk.END, str(s) + NL)
            text_log.see(tk.END)
        except Exception:
            pass
    try:
        traj_log_output.insert(tk.END, str(s) + NL)
        traj_log_output.see(tk.END)
    except Exception:
        pass
    try:
        if str(s).strip():
            traj_status_var.set(str(s))
    except Exception:
        pass
    try:
        root.update_idletasks()
    except Exception:
        pass

# ============================================================
# 连接（只连一次，复用）
# ============================================================
def ensure_connected():
    global _connected
    if _connected:
        return True
    try:
        robot.Connect()
        time.sleep(1.5)
        status, msg = robot.ConnectedState()
        log("连接状态: %s, %s" % (status, msg))
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        log("RunMode: %s" % RDK.RunMode())
        if status < 0:
            _connected = False
            log("机器人连接未建立，状态=%s：%s" % (status, msg))
            return False
        _connected = True
        return True
    except Exception as e:
        log("连接失败: %s" % e)
        return False

# ============================================================
# 解析坐标
# ============================================================
def parse_points():
    if not text_points:
        return []
    raw = text_points.get("1.0", tk.END)
    points = []
    for line in raw.strip().split(NL):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            vals = [float(v.strip()) for v in line.split(",")]
            if len(vals) >= 6:
                points.append(vals[:6])
        except ValueError:
            pass
    return points

# ============================================================
# 读取当前位置
# ============================================================
def read_current(entries=None):
    try:
        pose = current_flange_pose()
        v = pose_to_fanuc(pose)
        log("")
        log("当前法兰（不含工具）：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(v[:6]))
    except Exception as e:
        log("读取失败：%s" % e)

def fill_current(entries=None):
    try:
        pose = current_flange_pose()
        v = pose_to_fanuc(pose)
        if entries:
            for e, val in zip(entries, v):
                e.delete(0, tk.END)
                e.insert(0, "%.3f" % val)
        log("当前法兰（不含工具）已填入")
    except Exception as e:
        log("读取失败：%s" % e)

# ============================================================
# IK 检测
# 注意：SolveIK 显式使用当前 Tool + Reference，和 MoveL/MoveJ 保持一致。
# ============================================================
def check_ik_single(entries=None):
    if not entries:
        return
    try:
        values = [float(e.get()) for e in entries]
    except ValueError:
        log("输入无效")
        return

    x, y, z, rx, ry, rz = values
    target = fanuc_to_pose(x, y, z, rx, ry, rz)
    log("")
    log("目标：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % (x, y, z, rx, ry, rz))

    try:
        tool_pose = robot.PoseTool()
        frame_pose = robot.PoseFrame()
        joints = robot.SolveIK(target, tool=tool_pose, reference=frame_pose)
        if joints is None:
            log("IK 不可达")
        else:
            q = joints.list()
            if len(q) < 6:
                log("IK 返回关节数量异常：%d，原始数据=%r" % (len(q), q))
                return
            log("IK 可达")
            log("  关节：J1=%.2f J2=%.2f J3=%.2f J4=%.2f J5=%.2f J6=%.2f" % tuple(q[:6]))
    except Exception as e:
        log("检测失败：%s" % e)

def check_all_ik():
    points = parse_points()
    if not points:
        log("没有有效点")
        return

    log("")
    log("========== 检测全部 %d 个点 ==========" % len(points))
    all_ok = True
    for i, p in enumerate(points):
        try:
            target = fanuc_to_pose(*p)
            joints = robot.SolveIK(target, tool=robot.PoseTool(), reference=robot.PoseFrame())
            if joints is None:
                log("  P%d: 不可达" % (i+1))
                all_ok = False
            else:
                q = joints.list()
                if len(q) < 6:
                    raise ValueError("IK 返回关节数量异常: %d, raw=%r" % (len(q), q))
                log("  P%d: 可达  J1=%.1f J2=%.1f J3=%.1f J4=%.1f J5=%.1f J6=%.1f" % (i+1, *q[:6]))
        except Exception as e:
            log("  P%d: 检测失败 %s" % (i+1, e))
            all_ok = False
    if all_ok:
        log("全部 %d 个点可达" % len(points))
    else:
        log("存在不可达点，执行时会跳过")

# ============================================================
# 执行单点
# ============================================================
def execute_single(entries=None, mtype="MoveL"):
    if not entries:
        return
    try:
        values = [float(e.get()) for e in entries]
    except ValueError:
        log("输入无效")
        return

    x, y, z, rx, ry, rz = values
    target = fanuc_to_pose(x, y, z, rx, ry, rz)
    log("")
    log("目标：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % (x, y, z, rx, ry, rz))

    try:
        tool_pose = robot.PoseTool()
        frame_pose = robot.PoseFrame()
        joints = robot.SolveIK(target, tool=tool_pose, reference=frame_pose)
        if joints is None:
            log("IK 不可达，取消执行")
            return
        q = joints.list()
        if len(q) < 6:
            log("IK 返回关节数量异常：%d，取消执行；原始数据=%r" % (len(q), q))
            return
        log("IK 可达：J1=%.2f J2=%.2f J3=%.2f J4=%.2f J5=%.2f J6=%.2f" % tuple(q[:6]))
    except Exception as e:
        log("IK 检查失败：%s" % e)
        return

    if not ensure_connected():
        return

    try:
        robot.setPoseFrame(robot.PoseFrame())
        robot.setPoseTool(robot.PoseTool())
        robot.setSpeed(ROBOT_SPEED)
        log("发送 %s..." % mtype)
        if mtype == "MoveJ":
            robot.MoveJ(target)
        else:
            robot.MoveL(target)
        log("执行完成")
    except Exception as e:
        log("失败: %s: %s" % (type(e).__name__, e))

# ============================================================
# 连续运动核心函数（整段移植自仿真脚本《机械臂TCP仿真.py》的最新连续运动逻辑；
# 判定/算法完全一致，只做“仿真 -> 实机”替换：速度用本文件的 ROBOT_SPEED、
# 总开关为 ALLOW_MOTION、运行模式判断一律改成 RUNMODE_RUN_ROBOT，
# 并在执行前用 ensure_connected() 连接真实机械臂。）
# ============================================================
def refresh_record_list(record_text, trajectory_records):
    if record_text is None:
        return
    record_text.delete("1.0", tk.END)
    for i, rec in enumerate(trajectory_records, 1):
        kind = rec["type"]
        vals = rec["values"]
        if kind == "TCP":
            if rec.get("singular", False):
                sd = int(rec.get("j6_delta", 180))
                line = f"P{i:<3} [法兰-特异点 J6优先{sd:+d}°/可反向] X={vals[0]:9.3f} Y={vals[1]:9.3f} Z={vals[2]:9.3f} Rx={vals[3]:8.3f} Ry={vals[4]:8.3f} Rz={vals[5]:8.3f}\n"
            else:
                line = f"P{i:<3} [法兰]    X={vals[0]:9.3f} Y={vals[1]:9.3f} Z={vals[2]:9.3f} Rx={vals[3]:8.3f} Ry={vals[4]:8.3f} Rz={vals[5]:8.3f}\n"
        else:
            line = f"P{i:<3} [JNT]   J1={vals[0]:8.3f} J2={vals[1]:8.3f} J3={vals[2]:8.3f} J4={vals[3]:8.3f} J5={vals[4]:8.3f} J6={vals[5]:8.3f}\n"
        record_text.insert(tk.END, line)

def _parse_six_from_entries(entries, label):
    if not entries or len(entries) != 6:
        log(f"{label}输入框异常：需要 6 个值")
        return None
    try:
        vals = [float(e.get().strip()) for e in entries]
    except (ValueError, AttributeError):
        log(f"{label}输入无效：6 个值必须全部为数字")
        return None
    if not all(math.isfinite(v) for v in vals):
        log(f"{label}输入无效：不能包含 NaN 或无穷值")
        return None
    return vals

def _check_tcp_reachable(vals):
    """检查单个 TCP 点 IK 是否可达，返回 (True, target, joints)。"""
    try:
        target = fanuc_values_to_pose(*vals)
        joints = robot.SolveIK(_tcp_target_to_flange(target))
        if joints is None:
            log("法兰 IK：不可达")
            return False, None, None
        q = joints.list()
        if len(q) < 6:
            log(f"法兰 IK：返回关节数量异常：{q}")
            return False, None, None
        log("法兰 IK：可达")
        log(f"  IK关节：J1={q[0]:.2f} J2={q[1]:.2f} J3={q[2]:.2f} J4={q[3]:.2f} J5={q[4]:.2f} J6={q[5]:.2f}")
        return True, target, q[:6]
    except Exception as e:
        log(f"法兰 IK 检查失败：{type(e).__name__}: {e}")
        return False, None, None

def _check_tcp_segment_continuous(prev_vals, curr_vals, segment_index, samples=20):
    """检查相邻 TCP 点间插补路径的 IK 连续可达性"""
    if prev_vals is None:
        return True
    log(f"开始检查 P{segment_index-1} -> P{segment_index} 的法兰连续 IK（{samples+1} 个采样点）")
    for k in range(samples + 1):
        t = k / samples
        vals = [prev_vals[i] + (curr_vals[i] - prev_vals[i]) * t for i in range(6)]
        try:
            pose = fanuc_values_to_pose(*vals)
            joints = robot.SolveIK(_tcp_target_to_flange(pose))
            if joints is None:
                log(f"  P{segment_index-1} -> P{segment_index}：第 {k+1}/{samples+1} 个采样点 IK 不可达，t={t:.3f}")
                log(f"  法兰：X={vals[0]:.3f} Y={vals[1]:.3f} Z={vals[2]:.3f} Rx={vals[3]:.3f} Ry={vals[4]:.3f} Rz={vals[5]:.3f}")
                return False
            q = joints.list()
            if len(q) < 6:
                log(f"  P{segment_index-1} -> P{segment_index}：采样点 IK 返回异常：{q}")
                return False
        except Exception as e:
            log(f"  P{segment_index-1} -> P{segment_index}：采样点 IK 检查失败：{type(e).__name__}: {e}")
            return False
    log(f"P{segment_index-1} -> P{segment_index}：连续 IK 检查通过")
    return True

def add_and_check_trajectory_point(traj_type, traj_entries, trajectory_records, record_text, log, singular_var=None, j6_direction_var=None):
    kind = traj_type.get()
    vals = _parse_six_from_entries(traj_entries, kind)
    if vals is None:
        return

    log("")
    log(f"========== 检查连续运动第 {len(trajectory_records)+1} 点 ==========")

    # 末端特异点：用户明确声明该点只需要末端绕自身轴转 180°。
    # 因此完全跳过 SolveIK/连续 IK 检查，执行时只让 J6 转 ±180°。
    is_singular = bool(singular_var.get()) if singular_var is not None else False
    j6_delta = int(j6_direction_var.get()) if j6_direction_var is not None else 180

    if kind == "TCP" and is_singular:
        if not trajectory_records:
            log("末端特异点不能作为第一个点：需要先有一个起始运动点。")
            return
        if trajectory_records[-1]["type"] != "TCP" or trajectory_records[-1].get("singular", False):
            log("末端特异点前一项必须是普通法兰点；否则无法保证只是末端原地旋转 180°。")
            return
        prev_vals = trajectory_records[-1]["values"]
        pos_err = math.sqrt(sum((vals[k] - prev_vals[k]) ** 2 for k in range(3)))
        if pos_err > 1e-3:
            log("末端特异点未加入：它的 XYZ 必须与前一个普通法兰点相同。")
            log(f"  与前一点位置差：{pos_err:.6f} mm")
            log("  特异点的设计前提是：只改变末端绕自身轴的姿态，不改变法兰位置。")
            return
        try:
            target = fanuc_values_to_pose(*vals)
        except Exception as e:
            log(f"末端特异点姿态转换失败：{type(e).__name__}: {e}")
            return

        trajectory_records.append({
            "type": "TCP",
            "values": vals[:],
            "target": target,
            "joints": None,
            "singular": True,
            "j6_delta": j6_delta,
        })
        log(f"P{len(trajectory_records)} [法兰-特异点]：已加入，跳过 IK。")
        log(f"  执行时保持 J1~J5 不变，J6优先转 {j6_delta:+d}°；整段不可行时尝试反向。")
        log("  请确保该点与前一点相比确实只是末端绕自身轴旋转 180°。")
        refresh_record_list(record_text, trajectory_records)
        if singular_var is not None:
            singular_var.set(False)
        return

    if kind == "TCP":
        ok, target, joints = _check_tcp_reachable(vals)
        if not ok:
            log("该法兰点未加入轨迹。")
            return

        # 普通 TCP 与前一个普通 TCP 之间做连续 IK 检查。
        # 如果前一个点是末端特异点，则特异点本身跳过 IK；当前点从这里开始重新做普通 SolveIK，
        # 因此不把“特异点姿态 -> 当前姿态”当成普通 TCP 笛卡尔插补段。
        if trajectory_records and trajectory_records[-1]["type"] == "TCP" and not trajectory_records[-1].get("singular", False):
            prev_vals = trajectory_records[-1]["values"]
            segment_no = len(trajectory_records) + 1
            if not _check_tcp_segment_continuous(prev_vals, vals, segment_no, samples=20):
                log(f"P{segment_no} [法兰]：上一法兰点到当前法兰点的连续 IK 检查失败，该点未加入轨迹。")
                return

        trajectory_records.append({
            "type": "TCP",
            "values": vals[:],
            "target": target,
            "joints": joints,
        })
        log(f"P{len(trajectory_records)} [法兰]：检查通过，已加入连续运动。")
    else:
        # 关节点：角度规范到 (-180, 180]
        corrected = [((v + 180.0) % 360.0) - 180.0 for v in vals]
        corrected = [180.0 if v <= -180.0 else v for v in corrected]
        if corrected != vals:
            log("关节点角度已自动纠正到 (-180°, 180°]：")
            log("  原始：" + "  ".join(f"J{i+1}={vals[i]:+.3f}°" for i in range(6)))
            log("  修正：" + "  ".join(f"J{i+1}={corrected[i]:+.3f}°" for i in range(6)))
        trajectory_records.append({
            "type": "JOINT",
            "values": corrected[:],
            "target": None,
            "joints": corrected[:],
        })
        log(f"P{len(trajectory_records)} [JNT]：未做 IK 可达性检查，角度规范化后已加入连续运动。")

    refresh_record_list(record_text, trajectory_records)

def _write_values_to_traj_entries(values, label):
    if not traj_entries or len(traj_entries) != 6:
        log(f"连续运动输入框异常：无法写入当前{label}")
        return False
    for e, val in zip(traj_entries, values[:6]):
        e.delete(0, tk.END)
        e.insert(0, f"{val:.3f}")
    log(f"当前{label}已写入选项卡3输入框")
    return True

def read_current_tcp_to_traj(traj_type, traj_entries, log):
    try:
        pose = _trajectory_pose(_joints6())
        vals = pose_to_fanuc_values(pose)
        log("========== 读取当前法兰 -> 连续运动输入框 ==========")
        log(f"X={vals[0]:+.3f} Y={vals[1]:+.3f} Z={vals[2]:+.3f} Rx={vals[3]:+.3f} Ry={vals[4]:+.3f} Rz={vals[5]:+.3f}")
        if traj_type.get() != "TCP":
            traj_type.set("TCP")
            _update_traj_labels_and_defaults()
        return _write_values_to_traj_entries(vals, "TCP")
    except Exception as e:
        log(f"读取当前法兰失败：{type(e).__name__}: {e}")
        return False

def read_current_joints_to_traj(traj_type, traj_entries, log):
    try:
        joints = robot.SimulatorJoints()
        q = list(joints) if hasattr(joints, "__iter__") else [joints]
        if len(q) < 6:
            log(f"读取当前关节失败：SimulatorJoints 返回 {q}")
            return False
        q = q[:6]
        log("========== 读取当前关节 -> 连续运动输入框 ==========")
        log(f"J1={q[0]:+.3f} J2={q[1]:+.3f} J3={q[2]:+.3f} J4={q[3]:+.3f} J5={q[4]:+.3f} J6={q[5]:+.3f}")
        if traj_type.get() != "JOINT":
            traj_type.set("JOINT")
            _update_traj_labels_and_defaults()
        return _write_values_to_traj_entries(q, "关节")
    except Exception as e:
        log(f"读取当前关节失败：{type(e).__name__}: {e}")
        return False

def clear_trajectory_input(traj_type, traj_entries, log):
    if not traj_entries:
        return
    for e in traj_entries:
        e.delete(0, tk.END)
    if traj_type.get() == "TCP":
        defaults = ["0.000", "-241.500", "1047.000", "-90.000", "0.000", "180.000"]
    else:
        defaults = ["0.000"] * 6
    for e, val in zip(traj_entries, defaults):
        e.insert(0, val)
    log("当前输入已清空（恢复默认值）")

def delete_last_record(trajectory_records, record_text, log):
    if trajectory_records:
        rec = trajectory_records.pop()
        refresh_record_list(record_text, trajectory_records)
        log(f"已删除最后一点：P{len(trajectory_records)+1} [{rec['type']}]")
    else:
        log("当前没有可删除的连续运动点")

def clear_records(trajectory_records, record_text, log):
    trajectory_records.clear()
    refresh_record_list(record_text, trajectory_records)
    log("连续运动点列表已清空")

# ============================================================
# 新增：导入导出函数
# ============================================================
def export_trajectory(trajectory_records, log):
    """导出轨迹到 JSON 文件"""
    if not trajectory_records:
        log("没有可导出的轨迹点。")
        return
    filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if not filepath:
        return
    try:
        # 只导出类型和数值，不保存 target/joints（执行时重新计算）
        export_data = [{"type": rec["type"], "values": rec["values"], "singular": bool(rec.get("singular", False)), "j6_delta": int(rec.get("j6_delta", 180))} for rec in trajectory_records]
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        log(f"轨迹已导出到：{filepath}")
    except Exception as e:
        log(f"导出失败：{e}")

def import_trajectory(trajectory_records, record_text, log):
    """从 JSON 文件导入轨迹"""
    filepath = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if not filepath:
        return
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("文件内容不是列表格式")
        # 验证每个元素
        for item in data:
            if not isinstance(item, dict) or 'type' not in item or 'values' not in item:
                raise ValueError("每个点必须包含'type'和'values'字段")
            if item['type'] not in ('TCP', 'JOINT'):
                raise ValueError(f"不支持的type: {item['type']}")
            if not isinstance(item['values'], list) or len(item['values']) != 6:
                raise ValueError("values必须为长度为6的列表")
            for v in item['values']:
                if not isinstance(v, (int, float)):
                    raise ValueError(f"values中的值必须为数字: {v}")
        # 清空并加载（target/joints 置 None，执行时重新计算）
        trajectory_records.clear()
        for item in data:
            is_singular = bool(item.get("singular", False)) and item["type"] == "TCP"
            trajectory_records.append({
                "type": item["type"],
                "values": item["values"][:],
                "target": fanuc_values_to_pose(*item["values"]) if item["type"] == "TCP" else None,
                "joints": None,
                "singular": is_singular,
                "j6_delta": int(item.get("j6_delta", 180)) if is_singular else 0
            })
        refresh_record_list(record_text, trajectory_records)
        log(f"已从 {filepath} 导入 {len(data)} 个点")
    except Exception as e:
        log(f"导入失败：{e}")

# ============================================================
# MoveJ 兜底轨迹检查
# ============================================================
def _point_to_segment_distance(p, a, b):
    """3D点到线段距离，单位mm。"""
    ax, ay, az = a
    bx, by, bz = b
    px, py, pz = p
    ab = (bx-ax, by-ay, bz-az)
    ap = (px-ax, py-ay, pz-az)
    ab2 = ab[0]*ab[0] + ab[1]*ab[1] + ab[2]*ab[2]
    if ab2 < 1e-12:
        return math.sqrt((px-ax)**2 + (py-ay)**2 + (pz-az)**2)
    t = (ap[0]*ab[0] + ap[1]*ab[1] + ap[2]*ab[2]) / ab2
    t = max(0.0, min(1.0, t))
    q = (ax+t*ab[0], ay+t*ab[1], az+t*ab[2])
    return math.sqrt((px-q[0])**2 + (py-q[1])**2 + (pz-q[2])**2)


def _tcp_target_to_flange(target):
    """输入是参考系中的TCP；IK需要机器人基座系中的法兰位姿。"""
    return robot.PoseFrame() * target * invH(robot.PoseTool())


def _flange_target_description(target):
    flange = _tcp_target_to_flange(target)
    return ('换算后的法兰中心（基座系）XYZ=' +
            str(tuple(round(v, 3) for v in flange.Pos())) +
            ' mm，法兰Z轴方向=' + str(tuple(round(v, 6) for v in flange.VZ())))


def _tcp_position_from_joints(q):
    """关节角 -> 当前参考坐标系下的TCP位置，与轨迹输入使用同一坐标系。"""
    f = pose_to_fanuc_values(invH(robot.PoseFrame()) * robot.SolveFK(q) * robot.PoseTool())
    return (float(f[0]), float(f[1]), float(f[2]))


def _check_movej_tcp_trajectory(start_q, target_q, start_tcp_vals, target_tcp_vals, log, samples=30, max_deviation_mm=None):
    """
    在真正执行MoveJ之前，用关节空间线性插补采样，计算TCP轨迹相对
    起点-终点TCP直线段的最大偏离距离。

    目的：MoveL失败时，不再无条件MoveJ；只有MoveJ造成的TCP空间绕行
    没有超过允许值，才允许用MoveJ兜底。
    """
    if max_deviation_mm is None:
        max_deviation_mm = MOVEJ_FALLBACK_MAX_DEVIATION_MM

    start_q = [float(v) for v in start_q[:6]]
    target_q = [float(v) for v in target_q[:6]]
    a = (float(start_tcp_vals[0]), float(start_tcp_vals[1]), float(start_tcp_vals[2]))
    b = (float(target_tcp_vals[0]), float(target_tcp_vals[1]), float(target_tcp_vals[2]))

    log("开始检查 MoveJ 兜底轨迹：%d 个采样点，允许最大法兰偏离 %.3f mm" % (samples + 1, max_deviation_mm))
    max_dev = -1.0
    max_info = None

    for k in range(samples + 1):
        t = float(k) / float(samples)
        q = [start_q[j] + (target_q[j] - start_q[j]) * t for j in range(6)]
        try:
            p = _tcp_position_from_joints(q)
        except Exception as e:
            log("  MoveJ轨迹检查失败：第 %d/%d 个采样点 FK失败：%s: %s" % (k+1, samples+1, type(e).__name__, e))
            return False

        dev = _point_to_segment_distance(p, a, b)
        if dev > max_dev:
            max_dev = dev
            max_info = (k, t, q, p)

        if dev > max_deviation_mm:
            log("✕ MoveJ兜底轨迹拒绝：第 %d/%d 个采样点偏离法兰直线 %.3f mm > %.3f mm" %
                (k+1, samples+1, dev, max_deviation_mm))
            log("  t=%.3f  法兰=(%.3f, %.3f, %.3f)" % (t, p[0], p[1], p[2]))
            log("  因此不会执行这个MoveJ兜底动作，避免出现不可接受的大绕圈。")
            return False

    if max_info is not None:
        k, t, q, p = max_info
        log("✓ MoveJ兜底轨迹检查通过")
        log("  最大法兰偏离直线：%.3f mm（采样 %d/%d，t=%.3f）" % (max_dev, k+1, samples+1, t))
        log("  最大偏离点法兰=(%.3f, %.3f, %.3f)" % (p[0], p[1], p[2]))
    return True


# ============================================================
# 执行连续运动（MoveL失败时先检查MoveJ轨迹）
# ============================================================
def _collision_details():
    pairs = RDK.CollisionPairs()
    return '；'.join(f'{a.Name()}[连杆{ia}] 与 {b.Name()}[连杆{ib}]'
                    for a, b, ia, ib in pairs) or '路径碰撞或关节不可行'


def _disable_excluded_obstacle_collisions():
    """把 EXCLUDED_COLLISION_KEYWORDS 命中的工位对象从碰撞判断里摘掉。

    机器人本体（连杆 0~6）与所有工具对它的配对全部关闭，
    其它障碍物（安装台/地面）的判断不受影响。返回被排除的对象名列表。
    """
    excluded = []
    if not EXCLUDED_COLLISION_KEYWORDS:
        return excluded
    for obj in RDK.ItemList(ITEM_TYPE_OBJECT):
        name = obj.Name()
        if not any(key in name for key in EXCLUDED_COLLISION_KEYWORDS):
            continue
        for link in range(0, 7):
            RDK.setCollisionActivePair(COLLISION_OFF, robot, obj, link, 0)
        for tool in RDK.ItemList(ITEM_TYPE_TOOL):
            RDK.setCollisionActivePair(COLLISION_OFF, tool, obj)
        excluded.append(name)
    return excluded


def _enable_obstacle_checks():
    # 预检只在仿真模式下做（见 execute_recorded_trajectory 里的说明）：
    # 实机模式下这些测试接口会去问真机驱动（robot.Joints() 超时只回 1×1 的 [[0]]），
    # 也有把预检动作发到真机的风险。
    if RDK.RunMode() != RUNMODE_SIMULATE:
        raise RuntimeError('障碍物预检只允许在仿真模式（RUNMODE_SIMULATE）下执行：预检只动模型，不下发真机。')
    # 每次进入预检都清空预检缓存：缓存生命周期 = 单次预检规划，
    # 障碍物/工作站状态的变化在下一次预检即时生效。
    _plan_cache.clear()
    for name in ('安装台_650x650x80mm', '地面_禁止穿越'):
        obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
        if not obstacle.Valid():
            raise RuntimeError(f'缺少障碍物模型：{name}，请加载包含台子和地面的工作站。')
        if name == '安装台_650x650x80mm':
            if RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0) != 1:
                raise RuntimeError('无法配置安装台与固定底座的接触关系。')
        for link in range(1, 7):
            if RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0) != 1:
                raise RuntimeError(f'无法启用{name}与连杆{link}的碰撞检查。')
        for tool in RDK.ItemList(ITEM_TYPE_TOOL):
            parent = tool.Parent()
            while parent.Valid() and parent.item != robot.item:
                parent = parent.Parent()
            if parent.Valid() and RDK.setCollisionActivePair(COLLISION_ON, tool, obstacle) != 1:
                raise RuntimeError(f'无法启用{name}与工具的碰撞检查。')
    # 先打开全局碰撞检查，再单独关掉被排除对象的配对
    # （Collision_SetState 只管全局开关，不会覆盖下面的逐对设置）。
    RDK.setCollisionActive(COLLISION_ON)
    for name in _disable_excluded_obstacle_collisions():
        try:
            log(f'碰撞判断已排除：{name}（本阶段的临时设置，见 EXCLUDED_COLLISION_KEYWORDS）')
        except Exception:
            pass


def _check_single_joint_path(end):
    _enable_obstacle_checks()
    saved = _joints6()
    try:
        RDK.Command('Trace', 'Off')
        RDK.Render(False)
        if _movej_test_cached(saved, end, 1) != 0:
            raise ValueError('单点MoveJ路径被拒绝：' + _collision_details())
    finally:
        robot.setJoints(saved)
        RDK.Render(True)


def _trajectory_pose(q):
    return invH(robot.PoseFrame()) * robot.SolveFK(q) * robot.PoseTool()


def _linear_path_endpoint(start, target):
    """带结果缓存：分支重试时同一（起点, 目标）不重复计算。"""
    key = ('linear', _cache_key_joints(start), _cache_key_pose(target))
    if key in _plan_cache:
        return _plan_cache[key]
    result = _linear_path_endpoint_uncached(start, target)
    _plan_cache[key] = result
    return result


def _linear_path_endpoint_uncached(start, target):
    # 粗筛：10mm 采样点是 1mm 采样点的子集，粗筛失败则 1mm 细查必然失败，
    # 可直接拒绝；粗筛通过后再跑原有 1mm 细查，通过/拒绝判定与只跑 1mm 完全一致。
    status = robot.MoveL_Test(start, target, minstep_mm=10)
    if status == 0:
        status = robot.MoveL_Test(start, target, minstep_mm=1)
    if status != 0:
        return None, f'MoveL原生路径检查未通过（{status}）：' + _collision_details()
    # 本机MoveL_Test返回成功后Joints()可能为全零；从插补矩阵读取实际终点。
    # 碰撞判定已由上方同路径 1mm MoveL_Test 完成，此处仅提取终点关节，
    # 关闭碰撞检查提速（实测约快两个数量级）；整段权威碰撞复核仍在
    # _verify_obstacle_plan（碰撞开、1mm）进行。
    program = RDK.AddProgram('_TCP实机_路径预检', robot)
    try:
        program.setVisible(False)
        robot.setJoints(start)
        program.setPoseFrame(robot.PoseFrame())
        program.setPoseTool(robot.PoseTool())
        program.MoveJ(start)
        program.MoveL(target)
        message, matrix, status = program.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_OFF)
        if status < 0:
            return None, message
        end = matrix.tr().rows[-1][:6]
        error_pose = invH(target) * _trajectory_pose(end)
        if norm(error_pose.Pos()) > .01 or pose_angle(error_pose) > math.radians(.01):
            raise RuntimeError('路径预检返回的终点不匹配目标法兰。')
        return end, message
    finally:
        program.Delete()


def _obstacle_posture_key(q, reference=None):
    table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
    height = 0.0
    if table.Valid():
        elbow = invH(table.PoseAbs()) * robot.PoseAbs() * robot.JointPoses(q)[3]
        height = elbow.Pos()[2]
    return (-round(height, 6), sum((v-r)**2 for v, r in zip(q, reference or [0]*6)), tuple(q))


def _obstacle_joint_target(start, values, max_deviation=None, log=None):
    """带结果缓存：同一（起点, 目标, 偏离上限）的兜底选解不重复搜索。"""
    key = ('obstacle', _cache_key_joints(start), tuple(round(float(v), 6) for v in values[:6]),
           round(float(max_deviation), 6) if max_deviation is not None else None)
    if key in _plan_cache:
        cached = _plan_cache[key]
        if isinstance(cached, ValueError):
            raise cached
        return cached
    try:
        result = _obstacle_joint_target_uncached(start, values, max_deviation, log)
    except ValueError as exc:
        _plan_cache[key] = exc
        raise
    _plan_cache[key] = result
    return result


def _obstacle_joint_target_uncached(start, values, max_deviation=None, log=None):
    lower, upper, _ = robot.JointLimits()
    candidates = _trajectory_start_candidates([dict(type='TCP', values=values)], lower.list(), upper.list(), start)
    saved = _joints6()
    try:
        # 少量FK采样仅用于排序；不能替代后面的偏离复核与精细碰撞检查。
        a = _tcp_position_from_joints(start)
        table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
        base_to_table = invH(table.PoseAbs()) * robot.PoseAbs()
        ranked = []
        for end in candidates:
            deviation, height = 0.0, float('inf')
            for k in range(11):
                q = [x + (y-x)*k/10 for x, y in zip(start, end)]
                deviation = max(deviation, _point_to_segment_distance(
                    _tcp_position_from_joints(q), a, values[:3]))
                height = min(height, (base_to_table * robot.JointPoses(q)[3]).Pos()[2])
            if max_deviation is not None and deviation > max_deviation:
                continue
            # 20mm一档，避免为很小的偏离差反复搜索；同档优先抬高肘部。
            ranked.append(((int(deviation/20), -height,
                            sum(abs(y-x) for x, y in zip(start, end))), end))
        checked = 0
        for _, end in sorted(ranked, key=lambda entry: entry[0]):
            if max_deviation is not None and not _check_movej_tcp_trajectory(
                    start, end, pose_to_fanuc_values(_trajectory_pose(start)), values,
                    lambda msg: None, samples=100, max_deviation_mm=max_deviation):
                continue
            checked += 1
            if _movej_test_cached(start, end, .25) == 0:
                if log is not None:
                    log(f'MoveJ快速筛选：{len(candidates)}个候选，{len(ranked)}个通过粗筛，精查{checked}条后找到合格路径。')
                return end
        raise ValueError('所有候选关节路径均碰撞、超出偏离限制或没有有效逆解。')
    finally:
        robot.setJoints(saved)


def _verify_obstacle_plan(start, plan):
    program = RDK.AddProgram('_TCP实机_整段碰撞复核', robot)
    saved = _joints6()
    try:
        program.setVisible(False)
        program.setPoseFrame(robot.PoseFrame())
        program.setPoseTool(robot.PoseTool())
        program.MoveJ(start)
        for step in plan:
            for q in step['rewinds']:
                program.MoveJ(q)
            getattr(program, step['method'])(step['joints'])
        message, matrix, status = program.InstructionListJoints(
            mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        if status < 0:
            raise ValueError('整段碰撞复核未通过：' + message)
    finally:
        program.Delete()
        robot.setJoints(saved)


def _trajectory_start_candidates(records, lower, upper, reference=None):
    reference = _joints6() if reference is None else reference
    first_tcp = next((rec for rec in records if rec['type'] == 'TCP'), None)
    if first_tcp is None:
        return [None]
    pose = fanuc_values_to_pose(*first_tcp['values'])
    solutions = robot.SolveIK_All(_tcp_target_to_flange(pose))
    candidates = []
    for solution in solutions:
        q = [((float(v) + 180.0) % 360.0) - 180.0 for v in solution[:6]]
        if len(q) != 6:
            continue
        for turns6 in (0, -1, 1):
            candidate = q[:]
            candidate[5] += 360.0 * turns6
            if all(lower[j] <= candidate[j] <= upper[j] for j in range(6)):
                if not any(max(abs(a-b) for a, b in zip(candidate, old)) < 1e-6 for old in candidates):
                    candidates.append(candidate)
    # 同一姿态保留接近当前关节圈数的表示，避免强制归零导致大绕行。
    for q in candidates[:]:
        nearest = [min((v + 360*k for k in range(math.ceil((lower[j]-v)/360),
                       math.floor((upper[j]-v)/360)+1)), key=lambda a: abs(a-reference[j]))
                   for j, v in enumerate(q)]
        if not any(max(abs(a-b) for a, b in zip(nearest, old)) < 1e-6 for old in candidates):
            candidates.append(nearest)
    # 高度只是候选偏好，整段无碰撞才可执行。
    return sorted(candidates, key=lambda q: _obstacle_posture_key(q, reference))


def _checked_j6_rewinds(q, lower, upper, max_deviation):
    """返回可实际执行的整圈回绕列表（带缓存）；TCP空间偏离和碰撞都必须通过检查。"""
    key = ('rewinds', _cache_key_joints(q), tuple(round(float(v), 6) for v in lower[:6]),
           tuple(round(float(v), 6) for v in upper[:6]), round(float(max_deviation), 6))
    if key in _plan_cache:
        return [r[:] for r in _plan_cache[key]]
    results = []
    tcp = pose_to_fanuc_values(_trajectory_pose(q))
    for delta in (-360.0, 360.0):
        end = q[:]
        end[5] += delta
        if not lower[5] <= end[5] <= upper[5]:
            continue
        if not _check_movej_tcp_trajectory(q, end, tcp, tcp, lambda msg: None,
                                          samples=360, max_deviation_mm=max_deviation):
            continue
        if _movej_test_cached(q, end, 1) == 0:
            results.append(end)
    _plan_cache[key] = results
    return [r[:] for r in results]


def _plan_continuous_trajectory(records, max_deviation, log):
    _enable_obstacle_checks()
    if not math.isfinite(max_deviation) or max_deviation < 0:
        raise ValueError('MoveJ允许偏离必须是非负有限数。')
    for i, rec in enumerate(records):
        vals = rec['values']
        if rec['type'] not in ('TCP', 'JOINT') or len(vals) != 6 or not all(math.isfinite(v) for v in vals):
            raise ValueError(f'P{i+1}：点类型或六维数值无效。')
        if rec.get('singular', False):
            if rec['type'] != 'TCP' or i == 0 or records[i-1]['type'] != 'TCP' or records[i-1].get('singular', False):
                raise ValueError(f'P{i+1}：特异点必须紧跟普通法兰点。')
            if rec.get('j6_delta', 180) not in (-180, 180):
                raise ValueError(f'P{i+1}：J6方向必须为+180或-180。')
    saved = _joints6()
    lower, upper, _ = robot.JointLimits()
    lower, upper = lower.list(), upper.list()
    # 先检查点本身可达，避免后面的不可达点触发整段分支重复搜索。
    unreachable = []
    for i, rec in enumerate(records, 1):
        if rec['type'] == 'TCP' and not rec.get('singular', False):
            target = fanuc_values_to_pose(*rec['values'])
            if robot.SolveIK_All(_tcp_target_to_flange(target)).size(1) == 0:
                unreachable.append(f'P{i}：没有逆解；' + _flange_target_description(target))
    if unreachable:
        raise ValueError('目标点不可达，尚未搜索连接路径：' + '；'.join(unreachable))
    if _movej_test_cached(saved, saved, 1) != 0:
        raise ValueError('起始姿态已碰撞，不能自动规划脱离：' + _collision_details())
    candidates = _trajectory_start_candidates(records, lower, upper, saved)
    direction_choices = [(rec.get('j6_delta', 180), -rec.get('j6_delta', 180))
                         for rec in records if rec.get('singular', False)]
    last_error = '首个普通法兰点没有限位内的逆解。'
    try:
        RDK.Render(False)
        # 先穷举特异点转向的整段组合；都不可行才允许额外整圈回绕。
        for allow_rewind in (False, True):
            failed_prefixes = set()
            for seed, directions in ((s, d) for s in candidates for d in itertools.product(*direction_choices)):
                seed_key = tuple(seed or [])
                if any((seed_key, directions[:n]) in failed_prefixes for n in range(len(directions)+1)):
                    continue
                selected_directions = iter(directions)
                direction_count = 0
                q = saved[:]
                first_tcp = True
                plan = []
                try:
                    for i, rec in enumerate(records, 1):
                        target = fanuc_values_to_pose(*rec['values']) if rec['type'] == 'TCP' else None
                        method, fallback = 'MoveJ', False
                        rewinds = []
                        selected_delta = None
                        special = rec.get('singular', False)
                        if rec['type'] == 'JOINT':
                            end = rec['values'][:]
                        elif special:
                            selected_delta = next(selected_directions)
                            direction_count += 1
                            end = q[:]
                            end[5] += selected_delta
                            if not lower[5] <= end[5] <= upper[5]:
                                if not allow_rewind:
                                    raise ValueError(f'P{i}：J6 {selected_delta:+d}°超限，尝试其他转向组合。')
                                for rewound in _checked_j6_rewinds(q, lower, upper, max_deviation):
                                    if lower[5] <= rewound[5] + selected_delta <= upper[5]:
                                        rewinds.append(rewound[:])
                                        q = rewound
                                        end = q[:]
                                        end[5] += selected_delta
                                        break
                                else:
                                    raise ValueError(f'P{i}：指定J6转向会超限，且没有通过偏离/碰撞检查的回绕。')
                            # 只改变J6，用FK核对目标位姿，不对特异点调用逆解。
                            error_pose = invH(target) * _trajectory_pose(end)
                            if norm(error_pose.Pos()) > 1e-3 or pose_angle(error_pose) > math.radians(.01):
                                raise ValueError(f'P{i}：仅旋转J6无法到达所标注法兰位姿，请检查特异点标记/工具。')
                        elif first_tcp:
                            end = seed[:]
                            first_tcp = False
                        else:
                            end, detail = _linear_path_endpoint(q, target)
                            if end is None and allow_rewind and not rec.get('require_linear', False):
                                for rewound in _checked_j6_rewinds(q, lower, upper, max_deviation):
                                    end, detail = _linear_path_endpoint(rewound, target)
                                    if end is not None:
                                        rewinds.append(rewound[:])
                                        q = rewound
                                        break
                            if end is None and rec.get('require_linear', False):
                                raise ValueError(f'P{i}：退让/返回工作位要求保持朝向的MoveL，检查未通过：{detail}')
                            if end is not None:
                                method = 'MoveL'
                            else:
                                try:
                                    end = _obstacle_joint_target(q, rec['values'], max_deviation, log)
                                except ValueError as exc:
                                    raise ValueError(f'P{i}：MoveL不可行；MoveJ避障选解失败：{exc}') from exc
                                fallback = True
                        if not all(lower[j] <= end[j] <= upper[j] for j in range(6)):
                            raise ValueError(f'P{i}：关节超限，J6目标={end[5]:.3f}°。')
                        if method == 'MoveJ' and _movej_test_cached(q, end, 1) != 0:
                            raise ValueError(f'P{i}：MoveJ路径检查失败：' + _collision_details())
                        plan.append(dict(method=method, joints=end[:], special=special, fallback=fallback, rewinds=rewinds, j6_delta=selected_delta))
                        q = end[:]
                    _verify_obstacle_plan(saved, plan)
                    log(f'整段路径预检通过：{len(plan)}点；首个法兰点 J6={seed[5]:+.3f}°。' if seed else f'整段路径预检通过：{len(plan)}个关节点。')
                    return plan
                except ValueError as exc:
                    # 后续尚未执行的J6方向不会改变已失败的路径前缀。
                    failed_prefixes.add((seed_key, directions[:direction_count]))
                    last_error = str(exc)
                    log(f'候选分支未通过：{last_error}')
        raise ValueError('没有找到整段可行的关节分支。' + last_error)
    finally:
        robot.setJoints(saved)
        RDK.Render(True)


def _retreat_orientation_records(records):
    """加工点变姿态前退到 y=-750，变姿态后返回 y=-775。"""
    result = []
    previous = None
    for index, record in enumerate(records, 1):
        current = dict(record, values=record['values'][:])
        current['label'] = f'P{index}'
        if previous and previous['type'] == current['type'] == 'TCP':
            old, new = previous['values'], current['values']
            changed = pose_angle(invH(fanuc_values_to_pose(*old)) * fanuc_values_to_pose(*new)) > math.radians(.01)
            old_work, new_work = abs(old[1] + 775) < .001, abs(new[1] + 775) < .001
            if changed and (old_work or new_work):
                anchor = old if old_work else new
                retreat = dict(type='TCP', values=[anchor[0], -750., anchor[2]] + old[3:], singular=False,
                               label=f'P{index}前退让', require_linear=old_work)
                result.append(retreat)
                turn = dict(current, values=retreat['values'][:3] + new[3:], label=f'P{index}退让位换向')
                result.append(turn)
                current['singular'] = False
                current['require_linear'] = new_work
        result.append(current)
        previous = record
    return result


def execute_recorded_trajectory(trajectory_records, log):
    global simulation_running
    if simulation_running:
        log('已有运动正在运行，请等待结束。')
        return
    if not ALLOW_MOTION or not trajectory_records:
        log('当前禁止运动或没有轨迹点。')
        return
    simulation_running = True
    log('========== 实机连续运动：将在真实机械臂上执行，请确认工作空间无人无障碍 ==========')
    completed_count = 0
    trace_owned = False
    i = 0
    try:
        if not ensure_connected():
            raise RuntimeError('RoboDK 与机器人的连接未建立，本次未启动（请检查 RoboDK 里的机器人连接状态）。')
        if robot.Busy():
            raise RuntimeError('机器人正在执行其他动作，本次未启动。')
        trace_owned = True
        RDK.Command('Trace', 'Off')
        RDK.Command('Trace', 'Reset')
        records = _retreat_orientation_records(trajectory_records)
        log(f'工作位 y=-775，换向位 y=-750：{len(trajectory_records)}个原始点展开为{len(records)}个执行点。')
        # ★★ 整段路径预检全程在【仿真模式】下做（与《机械臂TCP仿真.py》一致）：
        #    MoveJ_Test / MoveL_Test / InstructionListJoints / setJoints 都只作用于 RoboDK 模型，
        #    绝不下发到真机。实机模式下这些接口既会去问真机驱动（robot.Joints() 超时只返回
        #    1×1 的 [[0]] ⇒ 后续按 6 个用就 IndexError），又有把预检动作发到真机的风险。
        #    只有下面的"正式实机运动"才切回 RUNMODE_RUN_ROBOT。
        RDK.setRunMode(RUNMODE_SIMULATE)
        start_joints = _joints6()
        robot.setJoints(start_joints)
        log('当前关节（SimulatorJoints）：J1=%.3f J2=%.3f J3=%.3f J4=%.3f J5=%.3f J6=%.3f' % tuple(start_joints))
        log(f'========== 整段路径预检：{len(records)}点（仿真模式，只动模型） ==========')
        plan = _plan_continuous_trajectory(records, float(movej_deviation_var.get()), log)
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        status, conn_msg = robot.ConnectedState()
        if status < 0:
            raise RuntimeError(f'预检已通过，但 RoboDK 与机器人的连接不可用（status={status}：{conn_msg}），未执行实机运动。')
        robot.setSpeed(ROBOT_SPEED)
        RDK.Command('Trace', 'Reset')
        RDK.Command('Trace', 'On')
        log('========== 正式实机运动：现在仅显示本次实际运动轨迹 ==========')
        for i, step in enumerate(plan, 1):
            if RDK.RunMode() != RUNMODE_RUN_ROBOT:
                raise RuntimeError('运行模式改变，停止运动。')
            for rewound in step['rewinds']:
                before = _joints6()
                log(f'P{i}前：实际MoveJ回绕J6 {rewound[5]-before[5]:+.0f}°（{before[5]:+.3f}° → {rewound[5]:+.3f}°），已通过偏离及碰撞检查。')
                robot.MoveJ(rewound)
                if max(abs(a-b) for a, b in zip(_joints6(), rewound)) > .1:
                    raise RuntimeError('回绕终点与预检关节不一致。')
            log(f'P{i}（{records[i-1].get("label", "")}）开始 {step["method"]}，J6目标={step["joints"][5]:+.3f}°')
            # 执行预检得到的关节分支；运行时异常立即停止，不把停止/通信异常当作兜底请求。
            getattr(robot, step['method'])(step['joints'])
            actual = _joints6()
            if max(abs(a-b) for a, b in zip(actual, step['joints'])) > .1:
                raise RuntimeError('实际关节与预检终点不一致。')
            completed_count += 1
            suffix = f'（仅J6 {step["j6_delta"]:+d}°，J1～J5保持不变）' if step['special'] else ('（偏离检查后兜底）' if step['fallback'] else '')
            log(f'P{i} -> {step["method"]} 执行完成{suffix}')
        log(f'========== 连续运动完成：{completed_count}/{len(plan)} 点 ==========')
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        log(f'✕ 连续运动停止：已完成{completed_count}点，阶段={"路径预检" if i == 0 else "P"+str(i)}；{type(exc).__name__}: {exc}')
        for line in tb.rstrip().splitlines():
            log('  ' + line)
        try:
            import os as _os, tempfile as _tempfile
            path = _os.path.join(_tempfile.gettempdir(), '法兰连续运动_异常.txt')
            with open(path, 'w', encoding='utf-8') as fp:
                fp.write(tb)
            log('  （完整堆栈已写入 %s）' % path)
        except Exception:
            pass
    finally:
        if trace_owned:
            RDK.Command('Trace', 'Off')
            RDK.Render(True)
        try:
            # 预检会把运行模式切到仿真，这里恢复本脚本声明的实机模式。
            RDK.setRunMode(RUNMODE_RUN_ROBOT)
        except Exception:
            pass
        simulation_running = False

# 保留旧函数名，避免其他代码调用失效。
def execute_trajectory():
    execute_recorded_trajectory(trajectory_records, log)


# ============================================================
# 实机关节运动
# ============================================================
def _joint_values_from_entries(entries):
    """从 GUI 读取 J1~J6 目标角度。单位：deg。"""
    if not entries or len(entries) != 6:
        log("目标关节输入框异常：需要 J1~J6 共 6 个")
        return None
    try:
        q = [float(e.get().strip()) for e in entries]
    except (ValueError, AttributeError):
        log("目标关节输入无效：J1~J6 必须全部填写数字")
        return None
    if not all(math.isfinite(v) for v in q):
        log("目标关节输入无效：不能包含 NaN 或无穷值")
        return None
    return q


def read_current_joints(entries=None):
    """读取 RoboDK Robot Item 当前关节值，并可直接填入 J1~J6 输入框。
    注意：这里读取的是 RoboDK 当前 Robot Item 的关节状态，不调用 CR5 控制器 GetAngle。
    """
    try:
        joints = robot.SimulatorJoints()
        q = list(joints) if hasattr(joints, "__iter__") else [joints]
        if len(q) < 6:
            log("读取当前关节失败：SimulatorJoints 返回 %r" % (q,))
            log("请确认 RoboDK 窗口中的机器人已经连接并显示实时关节角度。")
            return None

        q = q[:6]
        log("")
        log("========== RoboDK 当前关节 ==========")
        log("J1=%+.3f°  J2=%+.3f°  J3=%+.3f°" % tuple(q[:3]))
        log("J4=%+.3f°  J5=%+.3f°  J6=%+.3f°" % tuple(q[3:]))

        if entries and len(entries) == 6:
            for e, val in zip(entries, q):
                e.delete(0, tk.END)
                e.insert(0, "%.3f" % val)
            log("当前关节已填入 J1~J6 输入框")

        return q
    except Exception as e:
        log("读取 RoboDK 当前关节失败：%s: %s" % (type(e).__name__, e))
        return None


def fill_current_joints(entries=None):
    """当前 RoboDK 关节 -> 目标关节输入框。"""
    return read_current_joints(entries)


def execute_joint_target(entries=None):
    """按 GUI 输入的 J1~J6 目标角度直接执行实机 MoveJ，不经过 TCP/IK。"""
    q = _joint_values_from_entries(entries)
    if q is None:
        return

    log("")
    log("========================================")
    log("====== 实机指定关节角度 MoveJ ======")
    log("目标：J1=%+.3f°  J2=%+.3f°  J3=%+.3f°" % tuple(q[:3]))
    log("      J4=%+.3f°  J5=%+.3f°  J6=%+.3f°" % tuple(q[3:]))
    log("运动速度：%.1f" % ROBOT_SPEED)
    log("控制方式：RoboDK Robot Item -> RUNMODE_RUN_ROBOT -> MoveJ(q)")

    if not ensure_connected():
        log("实机关节运动取消：机器人未连接")
        return

    try:
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        log("RunMode：%s" % RDK.RunMode())
        robot.setSpeed(ROBOT_SPEED)
        log("发送 MoveJ 目标：%r" % q)
        robot.MoveJ(q)
        log("MoveJ 命令已发送，目标关节角度：%r" % q)
        log("========================================")
    except Exception as e:
        log("实机 MoveJ 失败：%s: %s" % (type(e).__name__, e))


def clear_joint_target(entries=None):
    if not entries:
        return
    for e in entries:
        e.delete(0, tk.END)
        e.insert(0, "0.000")
    log("目标关节输入已清零")

# ============================================================
# GUI
# ============================================================
root = tk.Tk()
root.title("RoboDK - 机械臂运动控制")
root.geometry("1200x750")
root.resizable(True, True)

tk.Label(root, text="Dobot CR5 运动控制", font=("Microsoft YaHei", 16, "bold")).pack(pady=10)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# ---- 选项卡 1：单点运动 ----
tab_single = ttk.Frame(notebook)
notebook.add(tab_single, text="单点运动")

frame_coord = tk.LabelFrame(tab_single, text="目标法兰（Fanuc 格式，不含工具）")
frame_coord.pack(fill=tk.X, padx=10, pady=10)

names = ["X (mm)", "Y (mm)", "Z (mm)", "Rx (deg)", "Ry (deg)", "Rz (deg)"]
defaults = ["0.000", "-241.500", "1047.000", "-90.000", "0.000", "180.000"]
entries_single = []

for i in range(6):
    tk.Label(frame_coord, text=names[i]).grid(row=0, column=i*2, padx=5, pady=10)
    e = tk.Entry(frame_coord, width=12)
    e.insert(0, defaults[i])
    e.grid(row=0, column=i*2+1, padx=5, pady=10)
    entries_single.append(e)

frame_mtype = tk.Frame(tab_single)
frame_mtype.pack(fill=tk.X, padx=10, pady=5)
move_type = tk.StringVar(value="MoveL")
tk.Radiobutton(frame_mtype, text="MoveL (直线)", variable=move_type, value="MoveL").pack(side=tk.LEFT, padx=10)
tk.Radiobutton(frame_mtype, text="MoveJ (关节)", variable=move_type, value="MoveJ").pack(side=tk.LEFT, padx=10)

btn_single_frame = tk.Frame(tab_single)
btn_single_frame.pack(fill=tk.X, padx=10, pady=5)

def _read_current():
    read_current(entries_single)
def _fill_current():
    fill_current(entries_single)
def _check_ik():
    check_ik_single(entries_single)
def _exec_single():
    execute_single(entries_single, move_type.get())

tk.Button(btn_single_frame, text="读取当前法兰", command=_read_current, width=15).pack(side=tk.LEFT, padx=3)
tk.Button(btn_single_frame, text="当前法兰 -> 输入框", command=_fill_current, width=20).pack(side=tk.LEFT, padx=3)
tk.Button(btn_single_frame, text="检测可达性", command=_check_ik, width=15, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=3)
tk.Button(btn_single_frame, text="执行运动", command=_exec_single, width=20,
          font=("Microsoft YaHei", 10, "bold"), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=3)


# ---- 选项卡 2：目标关节运动（实机） ----
tab_joint = ttk.Frame(notebook)
notebook.add(tab_joint, text="目标关节运动")

frame_joint = tk.LabelFrame(tab_joint, text="目标关节（deg）")
frame_joint.pack(fill=tk.X, padx=10, pady=10)

joint_names = ["J1 (deg)", "J2 (deg)", "J3 (deg)", "J4 (deg)", "J5 (deg)", "J6 (deg)"]
joint_defaults = ["0.000", "0.000", "0.000", "0.000", "0.000", "0.000"]
entries_joint = []

for i in range(6):
    tk.Label(frame_joint, text=joint_names[i]).grid(row=0, column=i*2, padx=5, pady=10)
    e = tk.Entry(frame_joint, width=12)
    e.insert(0, joint_defaults[i])
    e.grid(row=0, column=i*2+1, padx=5, pady=10)
    entries_joint.append(e)

btn_joint_frame = tk.Frame(tab_joint)
btn_joint_frame.pack(fill=tk.X, padx=10, pady=8)

def _read_current_joint_values():
    read_current_joints(entries_joint)

def _fill_current_joints():
    fill_current_joints(entries_joint)

def _exec_joint():
    execute_joint_target(entries_joint)

def _zero_joints():
    clear_joint_target(entries_joint)

tk.Button(btn_joint_frame, text="读取当前关节", command=_read_current_joint_values, width=14).pack(side=tk.LEFT, padx=3)
tk.Button(btn_joint_frame, text="当前关节 -> 输入框", command=_fill_current_joints, width=20).pack(side=tk.LEFT, padx=3)
tk.Button(btn_joint_frame, text="执行指定关节 MoveJ", command=_exec_joint, width=24,
          font=("Microsoft YaHei", 10, "bold"), bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=3)
tk.Button(btn_joint_frame, text="清零", command=_zero_joints, width=10).pack(side=tk.LEFT, padx=3)

tk.Label(tab_joint,
         text="输入 J1~J6 目标角度（deg），点击“执行指定关节 MoveJ”直接控制实机；不经过 TCP、Fanuc 转换或 IK。",
         fg="#555555").pack(anchor=tk.W, padx=15, pady=5)
tk.Label(tab_joint,
         text="安全提示：首次测试建议只改变一个关节、改变 5~10°，确认方向和角度定义正确后再进行大角度运动。",
         fg="#C62828").pack(anchor=tk.W, padx=15, pady=2)

# ============================================================
# 选项卡 3：连续运动（含导入导出）
# ============================================================
tab_traj = ttk.Frame(notebook)
notebook.add(tab_traj, text="连续运动")

# ---- 输入区域 ----
frame_traj_input = tk.LabelFrame(tab_traj, text="连续运动点输入：每次输入 1 个法兰位姿或 1 组关节角度，点击“检查并加入”")
frame_traj_input.pack(fill=tk.X, padx=10, pady=10)

type_frame = tk.Frame(frame_traj_input)
type_frame.pack(fill=tk.X, padx=8, pady=5)

tk.Label(type_frame, text="点类型：").pack(side=tk.LEFT, padx=3)

traj_type = tk.StringVar(value="TCP")

def _update_traj_labels_and_defaults():
    """切换 TCP/关节时更新标签和默认值"""
    names = ["X", "Y", "Z", "Rx", "Ry", "Rz"] if traj_type.get() == "TCP" else ["J1", "J2", "J3", "J4", "J5", "J6"]
    defaults = ["0.000", "-241.500", "1047.000", "-90.000", "0.000", "180.000"] if traj_type.get() == "TCP" else ["0.000"]*6
    for i, e in enumerate(traj_entries):
        for widget in traj_value_frame.grid_slaves(row=0, column=i*2):
            widget.configure(text=names[i])
        e.delete(0, tk.END)
        e.insert(0, defaults[i])

tk.Radiobutton(type_frame, text="法兰（X,Y,Z,Rx,Ry,Rz，不含工具）", variable=traj_type, value="TCP", command=_update_traj_labels_and_defaults).pack(side=tk.LEFT, padx=8)
tk.Radiobutton(type_frame, text="关节（J1~J6）", variable=traj_type, value="JOINT", command=_update_traj_labels_and_defaults).pack(side=tk.LEFT, padx=8)

# ---- 末端特异点设置 ----
singular_frame = tk.Frame(tab_traj)
singular_frame.pack(fill=tk.X, padx=10, pady=2)
traj_singular = tk.BooleanVar(value=False)
traj_j6_direction = tk.IntVar(value=180)
tk.Checkbutton(
    singular_frame,
    text="标记当前法兰位姿为末端特异点（跳过 IK，J6 直接转 180°）",
    variable=traj_singular
).pack(side=tk.LEFT, padx=3)
tk.Label(singular_frame, text="J6优先方向（不可行时自动反向）：").pack(side=tk.LEFT, padx=(15, 2))
tk.Radiobutton(singular_frame, text="+180°", variable=traj_j6_direction, value=180).pack(side=tk.LEFT)
tk.Radiobutton(singular_frame, text="-180°", variable=traj_j6_direction, value=-180).pack(side=tk.LEFT)

movej_check_frame = tk.Frame(tab_traj)
movej_check_frame.pack(fill=tk.X, padx=10, pady=2)
tk.Label(movej_check_frame, text="MoveJ兜底轨迹最大允许偏离法兰直线：").pack(side=tk.LEFT, padx=3)
movej_deviation_var = tk.DoubleVar(value=MOVEJ_FALLBACK_MAX_DEVIATION_MM)
tk.Entry(movej_check_frame, textvariable=movej_deviation_var, width=8).pack(side=tk.LEFT, padx=3)
tk.Label(movej_check_frame, text="mm（MoveL失败后，先检查MoveJ轨迹；超限则拒绝MoveJ）", fg="#555555").pack(side=tk.LEFT, padx=3)

traj_value_frame = tk.Frame(frame_traj_input)
traj_value_frame.pack(fill=tk.X, padx=8, pady=5)

traj_entries = []
tcp_defaults = ["0.000", "-241.500", "1047.000", "-90.000", "0.000", "180.000"]
for i in range(6):
    tk.Label(traj_value_frame, text=["X","Y","Z","Rx","Ry","Rz"][i]).grid(row=0, column=i*2, padx=3, pady=8)
    e = tk.Entry(traj_value_frame, width=12)
    e.grid(row=0, column=i*2+1, padx=4, pady=8)
    e.insert(0, tcp_defaults[i])
    traj_entries.append(e)

# ---- 连续运动按钮 ----
btn_traj_input = tk.Frame(tab_traj)
btn_traj_input.pack(fill=tk.X, padx=10, pady=5)

tk.Button(btn_traj_input, text="检查并加入当前点", command=lambda: add_and_check_trajectory_point(traj_type, traj_entries, trajectory_records, record_text, log, traj_singular, traj_j6_direction), width=22, bg="#2196F3", fg="white", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT, padx=3)
tk.Button(btn_traj_input, text="读取当前法兰并写入", command=lambda: read_current_tcp_to_traj(traj_type, traj_entries, log), width=20).pack(side=tk.LEFT, padx=3)
tk.Button(btn_traj_input, text="读取当前关节并写入", command=lambda: read_current_joints_to_traj(traj_type, traj_entries, log), width=20).pack(side=tk.LEFT, padx=3)
tk.Button(btn_traj_input, text="清空当前输入", command=lambda: clear_trajectory_input(traj_type, traj_entries, log), width=16).pack(side=tk.LEFT, padx=3)

tk.Label(tab_traj, text="普通法兰点用 IK 判断可达并检查连续段；关节点只做角度规范化。标记为末端特异点的法兰位姿跳过 IK，仅在执行时让 J6 转 ±180°，其后的普通法兰点重新正常 IK。", fg="#555555").pack(anchor=tk.W, padx=15, pady=3)

# ---- 已添加点列表 ----
frame_record = tk.LabelFrame(tab_traj, text="已检查通过的连续运动点（按加入顺序执行，可混合 法兰位姿 / 关节点）")
frame_record.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

record_text = tk.Text(frame_record, font=("Consolas", 10), height=6)
record_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ---- 点管理按钮 ----
btn_record_frame = tk.Frame(tab_traj)
btn_record_frame.pack(fill=tk.X, padx=10, pady=4)

tk.Button(btn_record_frame, text="删除最后一点", command=lambda: delete_last_record(trajectory_records, record_text, log), width=15).pack(side=tk.LEFT, padx=3)
tk.Button(btn_record_frame, text="清空全部点", command=lambda: clear_records(trajectory_records, record_text, log), width=15).pack(side=tk.LEFT, padx=3)
tk.Button(btn_record_frame, text="执行整段连续运动", command=lambda: execute_recorded_trajectory(trajectory_records, log), width=24, font=("Microsoft YaHei", 10, "bold"), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=3)

# ---------- 新增：导入导出按钮 ----------
tk.Button(btn_record_frame, text="导出轨迹", command=lambda: export_trajectory(trajectory_records, log), width=12).pack(side=tk.LEFT, padx=3)
tk.Button(btn_record_frame, text="导入轨迹", command=lambda: import_trajectory(trajectory_records, record_text, log), width=12).pack(side=tk.LEFT, padx=3)
# --------------------------------------

tk.Label(tab_traj, text="特异点保持J1～J5不变，直接MoveJ转动J6；整段检查±180°两方向，优先无需整圈回绕的方案。", fg="#555555").pack(anchor=tk.W, padx=15, pady=4)

traj_status_var = tk.StringVar(value="升级版：特异点J6自动选择±180°，优先避免整圈回绕。")
tk.Label(tab_traj, textvariable=traj_status_var, anchor=tk.W, wraplength=1100).pack(fill=tk.X, padx=15)
traj_log_frame = tk.LabelFrame(tab_traj, text="连续运动日志 / 停止原因")
traj_log_frame.pack(fill=tk.X, padx=10, pady=5)
traj_log_output = tk.Text(traj_log_frame, font=("Consolas", 10), height=5, wrap=tk.WORD)
traj_log_output.pack(side=tk.LEFT, fill=tk.X, expand=True)
traj_log_scroll = ttk.Scrollbar(traj_log_frame, command=traj_log_output.yview)
traj_log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
traj_log_output.configure(yscrollcommand=traj_log_scroll.set)

# ---- 日志区 ----
frame_log = tk.LabelFrame(root, text="日志")
frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

text_log = scrolledtext.ScrolledText(frame_log, font=("Consolas", 10), height=8)
text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ============================================================
# 启动
# ============================================================
log("机器人: " + robot.Name())
log("程序就绪。模式：RUNMODE_RUN_ROBOT + robot.Connect()")
log("坐标基准：本脚本输入/显示/记录的都是【法兰】位姿（不含末端工具）；运动前自动 法兰×工具。当前工具 = %s" % pose_to_fanuc(robot.PoseTool())[:6])
log("单点：输入法兰坐标 -> 检测可达性 -> 执行 MoveL/MoveJ")
log("目标关节：输入 J1~J6 -> 实机 MoveJ（不经过法兰换算/Fanuc 转换和 IK）")
log("连续运动：支持导入本脚本导出的JSON；普通法兰点使用已验证IK（缺少时仅做单点SolveIK）；末端特异点跳过IK仅J6±180°；实机执行不重复轨迹预检；MoveL失败直接用已验证IK解MoveJ兜底")
log("连续运动：已升级为【仿真脚本《机械臂TCP仿真.py》的最新连续运动逻辑】——实机执行前会完整重跑整段路径预检（IK/连续段/障碍物碰撞/MoveJ兜底偏离检查）；**预检全程在仿真模式下完成、只动 RoboDK 模型**，只有预检通过后的正式运动才切到 RUNMODE_RUN_ROBOT 下发真机。请务必先确认工作空间无人无障碍。")
if EXCLUDED_COLLISION_KEYWORDS:
    log("碰撞判断：工位对象名含【%s】的对象（当前=磨砂圆盘 磨砂圆柱_R180_H40）本阶段不参与碰撞判断；恢复办法见常量 EXCLUDED_COLLISION_KEYWORDS。" % "、".join(EXCLUDED_COLLISION_KEYWORDS))

root.mainloop()
