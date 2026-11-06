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

ROBOT_SPEED = 20.0
NL = chr(10)

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

def current_flange_pose():
    """当前【法兰】位姿（当前参考坐标系下，不含工具）。

    等价于 invH(PoseFrame) × Pose，但不引入工具量，因此工具的改动不会影响读数。
    """
    return invH(robot.PoseFrame()) * robot.SolveFK(robot.Joints())

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

# ============================================================
# 日志
# ============================================================
def log(s):
    print(s)
    if text_log:
        text_log.insert(tk.END, str(s) + NL)
        text_log.see(tk.END)
        root.update_idletasks()

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
# 连续运动：选项卡3直接输入 TCP / 关节点，逐点检查后加入轨迹
# ============================================================
trajectory_records = []
record_text = None
traj_entries = None
traj_type = None
singular_var = None
j6_direction_var = None


def _parse_six_from_entries(entries, label):
    if not entries or len(entries) != 6:
        log("%s输入框异常：需要 6 个值" % label)
        return None
    try:
        vals = [float(e.get().strip()) for e in entries]
    except (ValueError, AttributeError):
        log("%s输入无效：6 个值必须全部为数字" % label)
        return None
    if not all(math.isfinite(v) for v in vals):
        log("%s输入无效：不能包含 NaN 或无穷值" % label)
        return None
    return vals


def _check_tcp_reachable(vals):
    """检查单个 TCP 点 IK 是否可达，返回 (True, target, joints)。"""
    try:
        target = fanuc_to_pose(*vals)
        tool_pose = robot.PoseTool()
        frame_pose = robot.PoseFrame()
        joints = robot.SolveIK(target, tool=tool_pose, reference=frame_pose)

        if joints is None:
            log("法兰 IK：不可达")
            return False, None, None

        q = joints.list()
        if len(q) < 6:
            log("法兰 IK：返回关节数量异常：%r" % q)
            return False, None, None

        log("法兰 IK：可达")
        log("  IK关节：J1=%.2f J2=%.2f J3=%.2f J4=%.2f J5=%.2f J6=%.2f" % tuple(q[:6]))
        return True, target, q[:6]
    except Exception as e:
        log("法兰 IK 检查失败：%s: %s" % (type(e).__name__, e))
        return False, None, None


def _check_tcp_segment_continuous(prev_vals, curr_vals, segment_index, samples=20):
    """检查前一个 TCP 点到当前 TCP 点之间的整段插补路径 IK 连续可达性。

    暂不考虑障碍物，只对 TCP 位姿做线性插值，并对每个采样位姿执行 SolveIK。
    起点和终点也包含在采样检查中。
    """
    if prev_vals is None:
        return True

    log("开始检查 P%d -> P%d 的法兰连续 IK（%d 个采样点）" %
        (segment_index - 1, segment_index, samples + 1))

    tool_pose = robot.PoseTool()
    frame_pose = robot.PoseFrame()

    for k in range(samples + 1):
        t = float(k) / float(samples)
        vals = [prev_vals[i] + (curr_vals[i] - prev_vals[i]) * t for i in range(6)]
        try:
            pose = fanuc_to_pose(*vals)
            joints = robot.SolveIK(pose, tool=tool_pose, reference=frame_pose)
            if joints is None:
                log("  P%d -> P%d：第 %d/%d 个采样点 IK 不可达，t=%.3f" %
                    (segment_index - 1, segment_index, k + 1, samples + 1, t))
                log("  法兰：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(vals))
                return False
            q = joints.list()
            if len(q) < 6:
                log("  P%d -> P%d：第 %d 个采样点 IK 返回异常：%r" %
                    (segment_index - 1, segment_index, k + 1, q))
                return False
        except Exception as e:
            log("  P%d -> P%d：第 %d 个采样点 IK 检查失败：%s: %s" %
                (segment_index - 1, segment_index, k + 1, type(e).__name__, e))
            return False

    log("P%d -> P%d：连续 IK 检查通过" % (segment_index - 1, segment_index))
    return True


def _check_joint_reachable(q):
    """兼容旧代码：关节点不做可达性/限位检查，输入合法即可加入。"""
    return True


def refresh_record_list():
    if record_text is None:
        return

    record_text.delete("1.0", tk.END)

    for i, rec in enumerate(trajectory_records, 1):
        kind = rec["type"]
        vals = rec["values"]

        if kind == "TCP":
            mark = " [J6特异点 %s180°]" % ("+" if rec.get("j6_delta", 180) >= 0 else "-") if rec.get("singular", False) else ""
            record_text.insert(
                tk.END,
                "P%-3d [法兰]%s   X=%9.3f Y=%9.3f Z=%9.3f Rx=%8.3f Ry=%8.3f Rz=%8.3f%s" %
                (i, mark, *vals, NL)
            )
        else:
            record_text.insert(
                tk.END,
                "P%-3d [JNT]   J1=%8.3f J2=%8.3f J3=%8.3f J4=%8.3f J5=%8.3f J6=%8.3f%s" %
                (i, *vals, NL)
            )


def add_and_check_trajectory_point():
    """
    选项卡3逐点输入：
    - 普通法兰：立即做端点 IK，并检查与前一个普通法兰点之间的连续 IK。
    - TCP 末端特异点：跳过 IK；要求与前一个普通法兰点 XYZ 相同，执行时仅 J6 转 ±180°。
    - 关节：不做 IK/限位检查，只将角度规范到 (-180°, 180°]。
    注意：这些检查只在“加入点”时完成；正式实机执行时不再做轨迹预检。
    """
    kind = traj_type.get()
    vals = _parse_six_from_entries(traj_entries, kind)
    if vals is None:
        return

    log("")
    log("========== 检查连续运动第 %d 点 ==========" % (len(trajectory_records) + 1))

    is_singular = bool(singular_var.get()) if (kind == "TCP" and singular_var is not None) else False
    j6_delta = int(j6_direction_var.get()) if (j6_direction_var is not None) else 180

    if kind == "TCP" and is_singular:
        if not trajectory_records:
            log("末端特异点不能作为第一个点：需要先有一个起始运动点。")
            return
        prev = trajectory_records[-1]
        if prev["type"] != "TCP" or prev.get("singular", False):
            log("末端特异点前一项必须是普通法兰点。")
            return
        prev_vals = prev["values"]
        pos_err = math.sqrt(sum((vals[k] - prev_vals[k]) ** 2 for k in range(3)))
        if pos_err > 1e-3:
            log("末端特异点未加入：XYZ 必须与前一个普通法兰点相同。")
            log("  与前一点位置差：%.6f mm" % pos_err)
            return
        try:
            target = fanuc_to_pose(*vals)
        except Exception as e:
            log("末端特异点姿态转换失败：%s: %s" % (type(e).__name__, e))
            return

        trajectory_records.append({
            "type": "TCP", "values": vals[:], "target": target, "joints": None,
            "singular": True, "j6_delta": j6_delta,
        })
        log("P%d [法兰-特异点]：已加入，跳过 IK。" % len(trajectory_records))
        log("  执行时保持 J1~J5 不变，仅让 J6 转 %+d°。" % j6_delta)
        if singular_var is not None:
            singular_var.set(False)
        refresh_record_list()
        return

    if kind == "TCP":
        ok, target, joints = _check_tcp_reachable(vals)
        if not ok:
            log("该法兰点未加入轨迹。")
            return

        # 只在点加入阶段检查连续 IK；实机正式执行时不再重复预检。
        if trajectory_records and trajectory_records[-1]["type"] == "TCP" and not trajectory_records[-1].get("singular", False):
            prev_vals = trajectory_records[-1]["values"]
            segment_no = len(trajectory_records) + 1
            if not _check_tcp_segment_continuous(prev_vals, vals, segment_no, samples=20):
                log("P%d [法兰]：上一普通法兰点到当前点的连续 IK 检查失败，该点未加入轨迹。" % segment_no)
                return

        trajectory_records.append({
            "type": "TCP", "values": vals[:], "target": target, "joints": joints,
            "singular": False, "j6_delta": 0,
        })
        log("P%d [法兰]：检查通过，已加入连续运动。" % len(trajectory_records))
    else:
        corrected = []
        for v in vals:
            v = ((v + 180.0) % 360.0) - 180.0
            if v <= -180.0:
                v = 180.0
            corrected.append(v)
        if corrected != vals:
            log("关节点角度已自动纠正到 (-180°, 180°]：")
            log("  原始：" + "  ".join("J%d=%+.3f°" % (i + 1, vals[i]) for i in range(6)))
            log("  修正：" + "  ".join("J%d=%+.3f°" % (i + 1, corrected[i]) for i in range(6)))
        trajectory_records.append({
            "type": "JOINT", "values": corrected[:], "target": None, "joints": corrected[:],
            "singular": False, "j6_delta": 0,
        })
        log("P%d [JNT]：未做 IK 检查，角度规范化后已加入连续运动。" % len(trajectory_records))

    refresh_record_list()


def _write_values_to_traj_entries(values, label):
    if not traj_entries or len(traj_entries) != 6:
        log("连续运动输入框异常：无法写入当前%s" % label)
        return False
    for e, val in zip(traj_entries, values[:6]):
        e.delete(0, tk.END)
        e.insert(0, "%.3f" % float(val))
    log("当前%s已写入选项卡3输入框" % label)
    return True


def read_current_tcp_to_traj():
    """读取当前 RoboDK TCP，并写入选项卡3的 TCP 输入框。"""
    try:
        pose = current_flange_pose()
        vals = pose_to_fanuc(pose)
        log("========== 读取当前法兰 -> 选项卡3 ==========")
        log("X=%+.3f Y=%+.3f Z=%+.3f Rx=%+.3f Ry=%+.3f Rz=%+.3f" % tuple(vals))
        if traj_type.get() != "TCP":
            traj_type.set("TCP")
            _update_traj_labels_and_defaults()
        return _write_values_to_traj_entries(vals, "TCP")
    except Exception as e:
        log("读取当前法兰失败：%s: %s" % (type(e).__name__, e))
        return False


def read_current_joints_to_traj():
    """读取 RoboDK Robot Item 当前关节，并写入选项卡3的关节输入框。"""
    q = read_current_joints(None)
    if q is None or len(q) < 6:
        return False
    log("========== 读取当前关节 -> 选项卡3 ==========")
    if traj_type.get() != "JOINT":
        traj_type.set("JOINT")
        _update_traj_labels_and_defaults()
    return _write_values_to_traj_entries(q, "关节")


def clear_trajectory_input():
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




def import_trajectory():
    """
    从仿真程序导出的 JSON 轨迹文件导入到实机连续运动列表。

    重要：这里不做连续轨迹预检，不做 MoveJ TCP 轨迹预检。
    普通法兰 如果 JSON 中没有保存 IK 关节，则只针对该点单独 SolveIK，
    用于得到实机执行所需的目标关节；这不是连续轨迹预检。
    """
    filepath = filedialog.askopenfilename(
        title="导入仿真轨迹",
        defaultextension=".json",
        filetypes=[("JSON 轨迹文件", "*.json"), ("所有文件", "*.*")]
    )
    if not filepath:
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("轨迹文件顶层必须是列表。")

        imported = []
        for idx, item in enumerate(data, 1):
            if not isinstance(item, dict):
                raise ValueError("P%d 不是对象格式。" % idx)

            kind = str(item.get("type", "")).upper()
            if kind == "JNT":
                kind = "JOINT"
            if kind not in ("TCP", "JOINT"):
                raise ValueError("P%d type 不支持：%r" % (idx, item.get("type")))

            values = item.get("values")
            if not isinstance(values, list) or len(values) != 6:
                raise ValueError("P%d values 必须是长度为6的列表。" % idx)
            try:
                values = [float(v) for v in values]
            except (TypeError, ValueError):
                raise ValueError("P%d values 必须全部为数字。" % idx)
            if not all(math.isfinite(v) for v in values):
                raise ValueError("P%d values 不能包含 NaN 或无穷值。" % idx)

            is_singular = bool(item.get("singular", False)) and kind == "TCP"
            j6_delta = int(item.get("j6_delta", 180)) if is_singular else 0
            if is_singular and j6_delta not in (-180, 180):
                raise ValueError("P%d 特异点 j6_delta 只能是 +180 或 -180。" % idx)

            if kind == "JOINT":
                # 与手动输入保持一致：自动规范到 (-180,180]。
                corrected = []
                for v in values:
                    v = ((v + 180.0) % 360.0) - 180.0
                    if v <= -180.0:
                        v = 180.0
                    corrected.append(v)
                values = corrected
                imported.append({
                    "type": "JOINT", "values": values, "target": None,
                    "joints": values[:], "singular": False, "j6_delta": 0
                })
                continue

            target = fanuc_to_pose(*values)

            if is_singular:
                # 特异点严格要求前一项为普通法兰，且 XYZ 相同。
                if not imported:
                    raise ValueError("P%d 末端特异点不能作为第一个点。" % idx)
                prev = imported[-1]
                if prev["type"] != "TCP" or prev.get("singular", False):
                    raise ValueError("P%d 末端特异点前一项必须是普通法兰。" % idx)
                pos_err = math.sqrt(sum((values[k] - prev["values"][k]) ** 2 for k in range(3)))
                if pos_err > 1e-3:
                    raise ValueError("P%d 末端特异点 XYZ 必须与前一个普通法兰 相同，位置差 %.6f mm。" % (idx, pos_err))
                imported.append({
                    "type": "TCP", "values": values[:], "target": target,
                    "joints": None, "singular": True, "j6_delta": j6_delta
                })
                continue

            # 优先使用文件中可能保存的 IK；当前仿真脚本的 JSON 通常没有 joints，
            # 因此回退到“单点 SolveIK”，仅为了得到实机 MoveJ/MoveL 所需目标关节。
            q = item.get("joints")
            if isinstance(q, list) and len(q) >= 6:
                try:
                    q = [float(v) for v in q[:6]]
                    if not all(math.isfinite(v) for v in q):
                        q = None
                except (TypeError, ValueError):
                    q = None

            if q is None:
                joints = robot.SolveIK(
                    target, tool=robot.PoseTool(), reference=robot.PoseFrame()
                )
                if joints is None:
                    raise ValueError("P%d 普通法兰 单点 IK 无解，无法导入。" % idx)
                q = joints.list()
                if q is None or len(q) < 6:
                    raise ValueError("P%d 普通法兰 IK 返回关节数量异常：%r" % (idx, q))
                q = [float(v) for v in q[:6]]

            imported.append({
                "type": "TCP", "values": values[:], "target": target,
                "joints": q[:], "singular": False, "j6_delta": 0
            })

        trajectory_records.clear()
        trajectory_records.extend(imported)
        refresh_record_list()
        log("")
        log("========== 导入仿真轨迹 ==========")
        log("文件：%s" % filepath)
        log("已导入 %d 个轨迹点。" % len(imported))
        log("连续轨迹预检：未执行（按实机程序设计）。")
        log("普通法兰：仅在缺少保存IK时进行单点 SolveIK；不进行连续段预检。")
        log("末端特异点：跳过IK，仅保留 J6 ±180° 标记。")
        log("================================")
    except Exception as e:
        log("轨迹导入失败：%s: %s" % (type(e).__name__, e))

def delete_last_record():
    if trajectory_records:
        rec = trajectory_records.pop()
        refresh_record_list()
        log("已删除最后一点：P%d [%s]" %
            (len(trajectory_records) + 1, rec["type"]))
    else:
        log("当前没有可删除的连续运动点")


def clear_records():
    trajectory_records.clear()
    refresh_record_list()
    log("连续运动点列表已清空")


def execute_recorded_trajectory():
    """
    实机执行选项卡3轨迹。

    重要：不做仿真轨迹预检。TCP 的 IK/连续 IK 已在“检查并加入当前点”阶段完成，
    实机这里只负责按仿真已经验证过的顺序执行。

    普通法兰：第一个 TCP MoveJ，后续普通法兰 优先 MoveL；MoveL 失败后直接用已经保存的 IK 关节 MoveJ 兜底。
    末端特异点：跳过 IK，读取当前 RoboDK Robot Item 关节，仅 J6 转 ±180°。
    特异点后的普通法兰：重新使用该普通法兰 自己保存的 IK，正常 MoveL。
    关节点：直接 MoveJ。
    StoppedError: Robot not connected：继续视为本段结束标志。
    """
    if not trajectory_records:
        log("没有已检查通过的运动点，请先在选项卡3输入并加入点。")
        return

    log("")
    log("========== 执行实机连续运动：%d 个点 ==========" % len(trajectory_records))
    log("轨迹预检：跳过（已在仿真/加入点阶段完成）")

    if not ensure_connected():
        log("连续运动取消：机器人未连接")
        return

    try:
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        robot.setPoseFrame(robot.PoseFrame())
        robot.setPoseTool(robot.PoseTool())
        robot.setSpeed(ROBOT_SPEED)

        tcp_count = 0
        completed_count = 0

        for i, rec in enumerate(trajectory_records, 1):
            kind = rec["type"]
            vals = rec["values"]
            is_singular = bool(rec.get("singular", False))
            j6_delta = int(rec.get("j6_delta", 180))

            if kind == "TCP" and is_singular:
                move_name = "J6特异点"
            elif kind == "TCP":
                move_name = "MoveJ" if tcp_count == 0 else "MoveL"
            else:
                move_name = "MoveJ"

            log("")
            log("---- 开始执行 P%d [%s] -> %s ----" % (i, kind, move_name))

            try:
                if kind == "TCP":
                    if is_singular:
                        # 特异点：当前 RoboDK Robot Item 关节作为起点，保持 J1~J5，仅改变 J6。
                        current_q = list(robot.SimulatorJoints())
                        if len(current_q) < 6:
                            raise RuntimeError("特异点：RoboDK SimulatorJoints 返回关节数量不足6个：%r" % current_q)
                        current_q = current_q[:6]
                        q_special = current_q[:]
                        q_special[5] += float(j6_delta)
                        # 保持与前面关节点规范一致，避免无意义多圈累加。
                        q_special[5] = ((q_special[5] + 180.0) % 360.0) - 180.0
                        if q_special[5] <= -180.0:
                            q_special[5] = 180.0
                        log("P%d [法兰-特异点]：J6 %.3f° -> %.3f°，J1~J5保持不变" %
                            (i, current_q[5], q_special[5]))
                        robot.MoveJ(q_special)
                        tcp_count += 1
                    elif tcp_count == 0:
                        # 首个普通TCP：使用加入阶段已经得到的IK关节，避免再次SolveIK。
                        q = rec.get("joints")
                        if q is None or len(q) < 6:
                            raise RuntimeError("P%d：缺少已保存的 TCP IK 关节解。" % i)
                        robot.MoveJ(q[:6])
                        tcp_count += 1
                    else:
                        # 后续普通TCP：优先 MoveL。
                        target = rec.get("target")
                        q = rec.get("joints")
                        if target is None or q is None or len(q) < 6:
                            raise RuntimeError("P%d：缺少已保存的 TCP 目标位姿或 IK 关节解。" % i)
                        try:
                            robot.MoveL(target)
                        except Exception as e_l:
                            # 仿真已经检查过 MoveJ 的 TCP 轨迹，因此实机不再重复预检，直接用已验证的 IK 解兜底。
                            log("P%d [法兰] -> MoveL 失败：%s: %s" % (i, type(e_l).__name__, e_l))
                            log("P%d [法兰] -> 直接使用仿真已验证的 IK 关节解执行 MoveJ 兜底。" % i)
                            robot.MoveJ(q[:6])
                    
                else:
                    q = rec["values"][:6]
                    robot.MoveJ(q)

                completed_count += 1
                log("P%d [%s] -> %s 返回正常，进入下一段。" % (i, kind, move_name))

            except Exception as e:
                err_type = type(e).__name__
                err_text = str(e)
                if err_type == "StoppedError" and "Robot not connected" in err_text:
                    completed_count += 1
                    log("P%d [%s] -> %s 已结束。" % (i, kind, move_name))
                    log("收到结束标志：StoppedError: Robot not connected")
                    log("将该报错视为本段运动结束，继续执行下一段。")
                    continue

                log("P%d [%s] -> %s 执行失败：%s: %s" %
                    (i, kind, move_name, err_type, err_text))
                log("非预期错误，停止后续连续运动。")
                return

        log("")
        log("========== 实机连续运动执行完成：%d/%d 段 ==========" %
            (completed_count, len(trajectory_records)))

    except Exception as e:
        log("连续运动初始化失败：%s: %s" % (type(e).__name__, e))


# 保留旧函数名，避免其他代码调用失效。
def execute_trajectory():
    execute_recorded_trajectory()


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

# ---- 选项卡 3：连续运动 ----
tab_traj = ttk.Frame(notebook)
notebook.add(tab_traj, text="连续运动")

frame_traj_input = tk.LabelFrame(
    tab_traj,
    text="连续运动点输入：每次输入 1 个法兰位姿或 1 组关节角度，点击“检查并加入”"
)
frame_traj_input.pack(fill=tk.X, padx=10, pady=10)

type_frame = tk.Frame(frame_traj_input)
type_frame.pack(fill=tk.X, padx=8, pady=5)

tk.Label(type_frame, text="点类型：").pack(side=tk.LEFT, padx=3)

traj_type = tk.StringVar(value="TCP")
tk.Radiobutton(
    type_frame, text="法兰（X,Y,Z,Rx,Ry,Rz，不含工具）",
    variable=traj_type, value="TCP"
).pack(side=tk.LEFT, padx=8)

tk.Radiobutton(
    type_frame, text="关节（J1~J6）",
    variable=traj_type, value="JOINT"
).pack(side=tk.LEFT, padx=8)

traj_names_tcp = ["X", "Y", "Z", "Rx", "Ry", "Rz"]
traj_names_joint = ["J1", "J2", "J3", "J4", "J5", "J6"]

traj_entries = []

# ---- 末端特异点设置 ----
singular_var = tk.BooleanVar(value=False)
j6_direction_var = tk.IntVar(value=180)

singular_frame = tk.Frame(frame_traj_input)
singular_frame.pack(fill=tk.X, padx=8, pady=3)

tk.Checkbutton(
    singular_frame,
    text="末端特异点（跳过IK，仅J6转180°）",
    variable=singular_var
).pack(side=tk.LEFT, padx=3)

tk.Label(singular_frame, text="J6方向：").pack(side=tk.LEFT, padx=(15, 3))
tk.Radiobutton(singular_frame, text="+180°", variable=j6_direction_var, value=180).pack(side=tk.LEFT, padx=3)
tk.Radiobutton(singular_frame, text="-180°", variable=j6_direction_var, value=-180).pack(side=tk.LEFT, padx=3)

# 输入框单独放在 grid 子容器中。
# frame_traj_input 本身使用 pack 管理子控件，不能再直接对它的子控件使用 grid。
traj_value_frame = tk.Frame(frame_traj_input)
traj_value_frame.pack(fill=tk.X, padx=8, pady=5)

for i in range(6):
    tk.Label(
        traj_value_frame,
        text=traj_names_tcp[i]
    ).grid(row=0, column=i * 2, padx=3, pady=8)

    e = tk.Entry(traj_value_frame, width=12)
    e.grid(row=0, column=i * 2 + 1, padx=4, pady=8)
    traj_entries.append(e)

# 默认先按 TCP 输入显示
tcp_defaults = ["0.000", "-241.500", "1047.000", "-90.000", "0.000", "180.000"]
for e, val in zip(traj_entries, tcp_defaults):
    e.insert(0, val)


def _update_traj_labels_and_defaults():
    """切换 TCP/关节输入时，更新标签和默认值。"""
    names = traj_names_tcp if traj_type.get() == "TCP" else traj_names_joint
    defaults = (
        tcp_defaults
        if traj_type.get() == "TCP"
        else ["0.000"] * 6
    )

    for i, e in enumerate(traj_entries):
        # grid 上的 Label 位于当前列
        for widget in traj_value_frame.grid_slaves(row=0, column=i * 2):
            widget.configure(text=names[i])

        e.delete(0, tk.END)
        e.insert(0, defaults[i])


tk.Radiobutton(
    type_frame, text="法兰（X,Y,Z,Rx,Ry,Rz，不含工具）",
    variable=traj_type, value="TCP",
    command=_update_traj_labels_and_defaults
).pack_forget()

# 重新建立带 command 的两个单选按钮
for widget in list(type_frame.pack_slaves()):
    if isinstance(widget, tk.Radiobutton):
        widget.destroy()

tk.Radiobutton(
    type_frame, text="法兰（X,Y,Z,Rx,Ry,Rz，不含工具）",
    variable=traj_type, value="TCP",
    command=_update_traj_labels_and_defaults
).pack(side=tk.LEFT, padx=8)

tk.Radiobutton(
    type_frame, text="关节（J1~J6）",
    variable=traj_type, value="JOINT",
    command=_update_traj_labels_and_defaults
).pack(side=tk.LEFT, padx=8)

btn_traj_input = tk.Frame(tab_traj)
btn_traj_input.pack(fill=tk.X, padx=10, pady=3)

tk.Button(
    btn_traj_input,
    text="检查并加入当前点",
    command=add_and_check_trajectory_point,
    width=22,
    bg="#2196F3",
    fg="white",
    font=("Microsoft YaHei", 10, "bold")
).pack(side=tk.LEFT, padx=3)

tk.Button(
    btn_traj_input,
    text="读取当前法兰并写入",
    command=read_current_tcp_to_traj,
    width=20
).pack(side=tk.LEFT, padx=3)

tk.Button(
    btn_traj_input,
    text="读取当前关节并写入",
    command=read_current_joints_to_traj,
    width=20
).pack(side=tk.LEFT, padx=3)

tk.Button(
    btn_traj_input,
    text="清空当前输入",
    command=clear_trajectory_input,
    width=16
).pack(side=tk.LEFT, padx=3)

tk.Label(
    tab_traj,
    text="输入一个点后：法兰位姿用 IK 判断可达；关节点不做检查，输入合法后直接加入。只有法兰点检查通过的点或合法关节点才会加入下面列表。",
    fg="#555555"
).pack(anchor=tk.W, padx=15, pady=3)

frame_record = tk.LabelFrame(
    tab_traj,
    text="已检查通过的连续运动点（按加入顺序执行，可混合 法兰位姿 / 关节点）"
)
frame_record.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

record_text = tk.Text(frame_record, font=("Consolas", 10), height=10)
record_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

btn_record_frame = tk.Frame(tab_traj)
btn_record_frame.pack(fill=tk.X, padx=10, pady=4)

tk.Button(
    btn_record_frame, text="删除最后一点",
    command=delete_last_record, width=15
).pack(side=tk.LEFT, padx=3)

tk.Button(
    btn_record_frame, text="清空全部点",
    command=clear_records, width=15
).pack(side=tk.LEFT, padx=3)

tk.Button(
    btn_record_frame, text="导入轨迹",
    command=import_trajectory, width=14
).pack(side=tk.LEFT, padx=3)

tk.Button(
    btn_record_frame, text="执行整段连续运动",
    command=execute_recorded_trajectory,
    width=24,
    font=("Microsoft YaHei", 10, "bold"),
    bg="#4CAF50", fg="white"
).pack(side=tk.LEFT, padx=3)

tk.Label(
    tab_traj,
    text="执行：普通法兰点首点 MoveJ、后续优先 MoveL；MoveL 失败直接用已验证的 IK 解 MoveJ 兜底；末端特异点仅 J6 ±180°；关节点直接 MoveJ。实机不重复做轨迹预检。",
    fg="#555555"
).pack(anchor=tk.W, padx=15, pady=4)

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

root.mainloop()
