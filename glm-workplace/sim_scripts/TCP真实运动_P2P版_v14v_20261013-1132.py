# -*- coding: utf-8 -*-
"""
RoboDK 实机运动控制（基于 robodk_movej_diag.py 的成功模式）
- 单点：TCP 输入 -> IK 检测 -> MoveL/MoveJ 执行
- 连续轨迹：与TCP仿真同款（姿态退让、J6特异点±180°/自转360°、避障规划+缓存）
2026-10-09：连续运动逻辑对齐 机械臂TCP仿真_副本.py；预检偏离默认 50→500（与验证口径一致）
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
import queue as _queue_mod
_log_queue = _queue_mod.Queue()  # 后台线程日志经队列回流主线程，GUI 不冻结
LOG_PATH = r'D:\mydata\glm-workplace\sim_scripts\real_gui_log_p2p.txt'  # P2P版独立日志，不覆盖v13黑匣子
LOG_VERSION = 'v14v-20261013-1120'  # ★ v14u-fix（2026-10-13 11:20）：法兰补偿MOVL「直发失败 ⇒ 自动回退细分途经点路径」，不再直接抛错停机。
# 依据 10-13 11:05 实测：P9 直发后 60s 仍距目标 10.69°（速度全 0，停止时关节=P8 构型），而 P5 同类直发 1.1s 即到位（残差 4.61mm/0.62°）
# ⇒ 结论：「法兰补偿直发」对某些点位（P9，段长 100.0mm）根本走不到——是该优化自身的【适用性边界】，不是任务失败。
#   细分途经点路径（waypoints）本就存在且已验证，故直发失败时降级重跑，任务继续；工具位姿在 finally 里已复原。
# 历史：v14t 等 6s 判「未观测到起步」（10:41 事后发现臂其实到了）→ v14u 提到 60s 目标锚定等待 → 仍超时 → v14v 加自动回退。
# 旧 v14u 备注：v14t 10:38 复跑判读——P9 起步延迟 >6s，「起点静止」与「完成静止」反馈不可区分，位置对目标才是唯一可靠锚点
# v12 黑匣子：原生崩溃时把 Python 调用栈转储到独立文件（被动，不影响逻辑）
# 注意：faulthandler.enable 只接受文件对象，传路径字符串会 AttributeError（v12 首版踩坑，已被 except 吞掉）
CRASH_PATH = r'D:\mydata\glm-workplace\sim_scripts\real_gui_crash.txt'
try:
    import faulthandler as _fh
    _crash_fp = open(CRASH_PATH, 'a', encoding='utf-8')
    _fh.enable(_crash_fp, all_threads=True)
except Exception:
    pass

def _file_log(s):
    try:
        import io as _io, time as _time
        with _io.open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(_time.strftime('%m-%d %H:%M:%S') + ' | ' + str(s) + NL)
    except Exception:
        pass


RDK = Robolink()

def fanuc_to_pose(x, y, z, rx, ry, rz):
    return Fanuc_2_Pose([x, y, z, rx, ry, rz])

def pose_to_fanuc(pose):
    return Pose_2_Fanuc(pose)

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
# v12 心跳：每5秒覆写一次小文件（时间戳+pid+日志末行），进程死亡时间一目了然
HEARTBEAT_PATH = r'D:\mydata\glm-workplace\sim_scripts\real_gui_heartbeat.txt'

def _start_heartbeat():
    import threading as _t, time as _time, os as _os, io as _io
    def _beat():
        while True:
            try:
                last = ''
                try:
                    with _io.open(LOG_PATH, 'r', encoding='utf-8') as f:
                        _lines = f.read().splitlines()
                        last = _lines[-1] if _lines else ''
                except Exception:
                    pass
                with _io.open(HEARTBEAT_PATH, 'w', encoding='utf-8') as f:
                    f.write('%s | pid=%d | alive\nlast: %s\n' % (
                        _time.strftime('%m-%d %H:%M:%S'), _os.getpid(), last[:150]))
            except Exception:
                pass
            _time.sleep(5.0)
    _t.Thread(target=_beat, daemon=True, name='gui_heartbeat').start()


def log(s):
    _file_log(s)  # 先落盘：即使后续 print 阻塞，磁盘日志也不受影响
    print(s)
    if text_log:
        try:
            _log_queue.put_nowait(str(s))
        except Exception:
            text_log.insert(tk.END, str(s) + NL)

# ============================================================
# 连接（只连一次，复用）
# ============================================================
def ensure_connected():
    global _connected
    try:
        status, msg = robot.ConnectedState()
        if status != ROBOTCOM_READY:
            if status >= 0:
                log('机器人未就绪，取消执行：' + str(msg))
                return False
            robot.Connect()
            # v14o：固定 1.5s 改为就绪探测（0.3s 轮询，最多 3s）：假断连恢复是每跳尾部
            # 停顿税的一部分；探测到就绪即返回，未就绪语义与旧版一致（返回 False）。
            for _ in range(10):
                time.sleep(0.3)
                status, msg = robot.ConnectedState()
                if status == ROBOTCOM_READY:
                    break
        _connected = status == ROBOTCOM_READY
        if not _connected:
            log('机器人连接未就绪：' + str(msg))
            return False
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        return True
    except Exception as exc:
        _connected = False
        log('连接失败：' + str(exc))
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
        pose = robot.Pose()
        v = pose_to_fanuc(pose)
        log("")
        log("当前 TCP：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(v[:6]))
    except Exception as e:
        log("读取失败：%s" % e)

def fill_current(entries=None):
    try:
        pose = robot.Pose()
        v = pose_to_fanuc(pose)
        if entries:
            for e, val in zip(entries, v):
                e.delete(0, tk.END)
                e.insert(0, "%.3f" % val)
        log("当前 TCP 已填入")
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
        log("存在不可达点，执行前整段预检将拒绝不通过的方案")

# ============================================================
# 执行单点
# ============================================================
def execute_single(entries=None, mtype="MoveL"):
    try:
        if not entries:
            return
        values = [float(e.get()) for e in entries]
        _execute_checked_real([dict(type='TCP', values=values)], single_method=mtype)
    except (ValueError, TypeError) as exc:
        log('单点输入无效：' + str(exc))


# ============================================================
# 连续运动：选项卡3直接输入 TCP / 关节点，逐点检查后加入轨迹
# ============================================================
trajectory_records = []
record_text = None
traj_entries = None
traj_type = None
singular_var = None
j6_direction_var = None
spin_var = None


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
            log("TCP IK：不可达")
            return False, None, None

        q = joints.list()
        if len(q) < 6:
            log("TCP IK：返回关节数量异常：%r" % q)
            return False, None, None

        log("TCP IK：可达")
        log("  IK关节：J1=%.2f J2=%.2f J3=%.2f J4=%.2f J5=%.2f J6=%.2f" % tuple(q[:6]))
        return True, target, q[:6]
    except Exception as e:
        log("TCP IK 检查失败：%s: %s" % (type(e).__name__, e))
        return False, None, None


def _check_tcp_segment_continuous(prev_vals, curr_vals, segment_index, samples=20):
    """检查前一个 TCP 点到当前 TCP 点之间的整段插补路径 IK 连续可达性。

    暂不考虑障碍物，只对 TCP 位姿做线性插值，并对每个采样位姿执行 SolveIK。
    起点和终点也包含在采样检查中。
    """
    if prev_vals is None:
        return True

    log("开始检查 P%d -> P%d 的 TCP 连续 IK（%d 个采样点）" %
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
                log("  TCP：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(vals))
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
            if rec.get("spin360", False):
                mark = " [J6自转360° %s]" % ("+" if rec.get("j6_delta", 360) >= 0 else "-")
            elif rec.get("singular", False):
                mark = " [J6特异点 %s180°]" % ("+" if rec.get("j6_delta", 180) >= 0 else "-")
            else:
                mark = ""
            record_text.insert(
                tk.END,
                "P%-3d [TCP]%s   X=%9.3f Y=%9.3f Z=%9.3f Rx=%8.3f Ry=%8.3f Rz=%8.3f%s" %
                (i, mark, *vals, NL)
            )
        else:
            record_text.insert(
                tk.END,
                "P%-3d [JNT]   J1=%8.3f J2=%8.3f J3=%8.3f J4=%8.3f J5=%8.3f J6=%8.3f%s" %
                (i, *vals, NL)
            )


def add_and_check_trajectory_point():
    values = _parse_six_from_entries(traj_entries, traj_type.get())
    if values is None:
        return
    kind = traj_type.get()
    is_singular = kind == 'TCP' and bool(singular_var.get())
    spin = is_singular and bool(spin_var.get())
    sign = 1 if int(j6_direction_var.get()) >= 0 else -1
    rec = dict(type=kind, values=values, singular=is_singular, spin360=spin,
               j6_delta=sign * (360 if spin else 180))
    try:
        records = _validated_records(trajectory_records + [rec])
    except ValueError as exc:
        log('点未加入：' + str(exc))
        return
    trajectory_records[:] = records
    refresh_record_list()
    if spin:
        log('P%d [TCP-J6自转360°]：已加入；执行时 J1~J5 不变，J6 %+d°。' % (len(records), sign * 360))
    else:
        log('点已加入；完整避障预检将在执行前进行。关节圈数按输入保留。')



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
        pose = robot.Pose()
        vals = pose_to_fanuc(pose)
        log("========== 读取当前 TCP -> 选项卡3 ==========")
        log("X=%+.3f Y=%+.3f Z=%+.3f Rx=%+.3f Ry=%+.3f Rz=%+.3f" % tuple(vals))
        if traj_type.get() != "TCP":
            traj_type.set("TCP")
            _update_traj_labels_and_defaults()
        return _write_values_to_traj_entries(vals, "TCP")
    except Exception as e:
        log("读取当前 TCP 失败：%s: %s" % (type(e).__name__, e))
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
    filepath = filedialog.askopenfilename(title='导入轨迹', defaultextension='.json', filetypes=[('JSON轨迹','*.json'),('所有文件','*.*')])
    if not filepath:
        return
    try:
        with open(filepath, encoding='utf-8') as f:
            records = _validated_records(json.load(f))
        trajectory_records[:] = records
        refresh_record_list()
        log(f'已导入{len(records)}点：{filepath}。执行前将从实机当前关节重新预检。')
    except Exception as exc:
        log('轨迹导入失败：' + str(exc))


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
    log('【点击】执行整段连续运动：当前列表 %d 点（转后台线程执行，窗口保持响应）' % len(trajectory_records))
    import threading
    def _worker():
        try:
            _execute_checked_real(list(trajectory_records))
        except Exception as exc:
            log('【线程异常】%s: %s' % (type(exc).__name__, exc))
    threading.Thread(target=_worker, daemon=True, name='real_exec').start()



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
    q = _joint_values_from_entries(entries)
    if q is not None:
        _execute_checked_real([dict(type='JOINT', values=q)])



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

# 与TCP仿真一致的预检核心；仅在仿真模式调用。
fanuc_values_to_pose = fanuc_to_pose
pose_to_fanuc_values = pose_to_fanuc
MOVEJ_FALLBACK_MAX_DEVIATION_MM = 50.0
# 预检缓存（与TCP仿真副本同款）：生命周期=单次预检规划，_enable_obstacle_checks 每次进入预检时清空。

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

def _tcp_target_to_flange(target):
    """输入是参考系中的TCP；IK需要机器人基座系中的法兰位姿。"""
    return robot.PoseFrame() * target * invH(robot.PoseTool())

def _flange_target_description(target):
    flange = _tcp_target_to_flange(target)
    return ('换算后的法兰中心（基座系）XYZ=' +
            str(tuple(round(v, 3) for v in flange.Pos())) +
            ' mm，法兰Z轴方向=' + str(tuple(round(v, 6) for v in flange.VZ())))


def _validated_records(data):
    if not isinstance(data, list) or not data:
        raise ValueError('轨迹必须是非空点列表。')
    result = []
    for i, rec in enumerate(data, 1):
        kind = str(rec.get('type', '')).upper()
        if kind == 'JNT':
            kind = 'JOINT'
        values = [float(v) for v in rec.get('values', [])]
        if kind not in ('TCP', 'JOINT') or len(values) != 6 or not all(math.isfinite(v) for v in values):
            raise ValueError(f'P{i}：类型或六维数值无效。')
        special = bool(rec.get('singular', False)) and kind == 'TCP'
        spin = special and bool(rec.get('spin360', False))
        raw_delta = int(rec.get('j6_delta', 360 if spin else 180)) if special else 0
        if special and (not result or result[-1]['type'] != 'TCP' or result[-1]['singular']):
            raise ValueError(f'P{i}：特异点前序或转向无效。')
        if special:
            if spin:
                if raw_delta not in (-360, 360):
                    raise ValueError(f'P{i}：J6自转方向必须为+360或-360。')
                if max(abs(a - b) for a, b in zip(values, result[-1]['values'])) > 1e-3:
                    raise ValueError(f'P{i}：J6自转360°特异点的六维数值必须与前一个TCP点完全相同。')
            elif raw_delta not in (-180, 180):
                raise ValueError(f'P{i}：J6方向必须为+180或-180。')
        delta = (360 if spin else 180) * (1 if raw_delta >= 0 else -1) if special else 0
        result.append(dict(type=kind, values=values, singular=special, spin360=spin, j6_delta=delta))
    return result


def _controller_feedback():
    # Dobot CR V3: 1440-byte real-time feedback; no command is sent on this socket.
    import socket
    import struct
    host, port, *_ = robot.ConnectionParams()
    if int(port) != 29999:
        raise RuntimeError('当前连接不是已验证的Dobot CR反馈协议。')
    previous = None
    with socket.create_connection((host, 30004), timeout=3.0) as connection:
        deadline = time.monotonic() + 3.0
        for _ in range(2):
            packet = bytearray()
            while len(packet) < 1440:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError('实机反馈读取超时。')
                connection.settimeout(remaining)
                part = connection.recv(1440 - len(packet))
                if not part:
                    raise RuntimeError('实机反馈连接已关闭。')
                packet.extend(part)
            length = struct.unpack_from('<Q', packet, 0)[0]
            marker = struct.unpack_from('<Q', packet, 48)[0]
            stamp = struct.unpack_from('<Q', packet, 32)[0]
            if length != 1440 or marker != 0x123456789ABCDEF:
                raise RuntimeError('实机反馈帧格式不匹配。')
            if previous is not None and stamp <= previous:
                raise RuntimeError('实机反馈时间戳未更新。')
            previous = stamp
        q = list(struct.unpack_from('<6d', packet, 192))   # ★真实关节角（v10定位，示教器交叉证实）；旧版误读432="连接基准+指令累加"的假值
        velocity = list(struct.unpack_from('<6d', packet, 480))
        mode = struct.unpack_from('<Q', packet, 24)[0]
        if not all(math.isfinite(v) for v in q + velocity):
            raise RuntimeError('实机反馈包含无效关节数值。')
        return q, velocity, mode


def _live_joints():
    if RDK.RunMode() != RUNMODE_RUN_ROBOT:
        raise RuntimeError('当前不是实机执行模式。')
    status, msg = robot.ConnectedState()
    if status != ROBOTCOM_READY:
        raise RuntimeError('机器人未就绪或已断连：' + str(msg))
    q, velocity, mode = _controller_feedback()
    # 阈值由 0.1 放宽到 1.0：实测静止时 J4/J3 的速度估计噪声可达 0.31°/s
    # （六轴角度 8 次采样完全相同），0.1 会把"其实已静止"误判为运动中而中止任务。
    if mode != 5 or max(abs(v) for v in velocity) > 1.0:
        raise RuntimeError('实机未处于使能静止状态，模式=%s。' % mode)
    return q


def _require_joints(expected):
    actual = _live_joints()
    if max(abs(a-b) for a,b in zip(actual, expected)) > 0.5:
        raise RuntimeError('关节反馈与预检状态不一致，停止后续命令。')


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


def _prepare_real_plan(records, start, deviation, single_method=None):
    RDK.setRunMode(RUNMODE_SIMULATE)
    try:
        RDK.Command('Trace', 'Off')
        robot.setJoints(start)
        if single_method is None:
            return _plan_continuous_trajectory(records, deviation, log)
        _enable_obstacle_checks()
        if robot.MoveJ_Test(start, start, minstep_deg=1) != 0:
            raise ValueError('起始姿态碰撞：' + _collision_details())
        values = records[0]['values']
        method, fallback = single_method, False
        if method not in ('MoveJ','MoveL'):
            raise ValueError('未知单点运动类型。')
        end = None
        waypoints = []
        if method == 'MoveL':
            end, _ = _linear_path_endpoint(start, fanuc_to_pose(*values))
            if end is not None:
                # v13：单点 MoveL 同样不信任驱动 MOVL（纯J6自转也一样，关节插值=同一路径），
                # 改细分途经点+MoveJ 执行
                waypoints = _linear_waypoints(start, fanuc_to_pose(*values))
                if waypoints:
                    log('单点 MoveL 改细分执行：%d 个途经点（步长≤%.0fmm）。' % (len(waypoints), LINEAR_SUBSTEP_MM))
                    log('单点 MoveL 途经跳（共%d跳）：%s' % (len(waypoints), [[float('%.2f' % v) for v in w] for w in waypoints]))
        if end is None:
            end = _obstacle_joint_target(start, values, deviation if method=='MoveL' else None)
            fallback, method = method=='MoveL', 'MoveJ'
        plan = [dict(method=method,joints=end,special=False,fallback=fallback,rewinds=[],j6_delta=None,waypoints=waypoints)]
        _verify_obstacle_plan(start, plan)
        return plan
    finally:
        robot.setJoints(start)
        RDK.Render(True)
        RDK.setRunMode(RUNMODE_RUN_ROBOT)  # 旧版 L615 有此行：预检后必须切回实机模式，否则 _live_joints 直接拒执行


def _wait_controller_static(max_wait_s=20.0, vel_threshold=0.5, samples=5, interval=0.3):
    """轮询30004反馈直到六轴静止（连续samples次速度<阈值），返回(关节, 是否静止)。

    v14o：断连分支以 samples=3/interval=0.2 调用（短跳≈1s，5×0.3s 静止确认占每跳
    尾部 ~1.5s，是停顿税大头）；默认 5×0.3s 供正常路径；20s 静止上限（真断连护栏）不动。"""
    t0 = time.time()
    quiet = 0
    last = None
    while time.time() - t0 < max_wait_s:
        actual, velocity, _mode = _controller_feedback()
        last = actual
        if max(abs(v) for v in velocity) < vel_threshold:
            quiet += 1
            if quiet >= samples:
                return last, True
        else:
            quiet = 0
        time.sleep(interval)
    return last, False


def _wait_arrival_then_static(target_joints, max_wait_s=20.0):
    """v14u：目标锚定的到位等待——直发后不再猜「起步了没」，只等「到没到」。

    背景（v14t 10:38 P9 实测）：直发指令起步延迟可 >6s，让位 6s 耗尽判「未执行」
    停止后，指令仍被控制器自行执行到精确目标（善后实测 J2 +10°/J3 +20°，余轴不动，
    宏未重发）——「起点静止」与「完成静止」在反馈上不可区分，位置对目标才是唯一
    可靠锚点（速度判据出局：三场停时 J4 0.06~0.42°/s 均为低于阈值的保持抖动）。
    本函数：距目标关节 ≤MOVL_ARRIVE_TOL_DEG 且速度<0.5°/s → 到位完成（此时已在
    目标，无需再做常规静止确认）；每 5s 一行进度日志（顺带实测真实延迟）；
    上限 MOVL_ARRIVE_WAIT_S 超时报「疑似未执行」停待判读；不重发铁律不变。
    target_joints=None → 退化为 _wait_controller_static()，行为与原先完全一致。"""
    if target_joints is not None:
        t0 = time.time()
        t_note = t0
        while True:
            fb = _controller_feedback()
            err = max(abs(a - b) for a, b in zip(fb[0], target_joints))
            if err <= MOVL_ARRIVE_TOL_DEG and max(abs(v) for v in fb[1]) < 0.5:
                log('MovL 直发到位确认：距目标关节%.2f°（%.1fs），验收继续。'
                    % (err, time.time() - t0))
                return fb[0], True
            if time.time() - t0 >= MOVL_ARRIVE_WAIT_S:
                raise RuntimeError(
                    'MovL 直发%.0fs仍未到位（距目标关节%.2f°），疑似未执行，停止待判读。'
                    % (MOVL_ARRIVE_WAIT_S, err))
            if time.time() - t_note >= 5.0:
                log('MovL 直发等待到位：%.0fs，距目标关节%.2f°，续等（不重发，上限%.0fs）。'
                    % (time.time() - t0, err, MOVL_ARRIVE_WAIT_S))
                t_note = time.time()
            time.sleep(0.5)
    return _wait_controller_static(max_wait_s=max_wait_s)


MOVE_OFFSET_TOL = 0.5   # 闭环补偿后的到位容差（°）


def _single_move_settle(method, target, require_joints=True, expect_target=None):
    """发一条运动指令并确认到位（v10：反馈字段已校正）。

    v14r：require_joints=False 仅供 MovL 直发调用点使用——断连分支的关节级 0.5°
    校验让位给外层法兰级粗验收（≤8mm/≤1°）+MoveJ 微纠偏收口（v14q 09:57 实机
    教训：MovL 直发必触发假断连，0.95° 固有残差在断连分支内即被拦停，外层验收
    根本没执行到）。其余护栏不变：20s 静止上限、重连失败仍停。

    v14u：断连分支改目标锚定到位等待 _wait_arrival_then_static——v14t 10:38 实测
    P9 起步延迟>6s（让位按设计耗尽判停），指令事后仍被控制器自行执行到精确目标
    （宏未重发）。「起点静止」不可判，唯一可靠锚点=位置对目标：距目标≤2°且静止
    即完成，上限 60s，每 5s 进度日志；超时报「疑似未执行」停。不重发铁律不变。

    历史结论：驱动一直正确执行绝对关节目标；此前"半路停止"源于旧反馈误读偏移432
    （那字段是"连接基准+指令累加"的假关节角，v7/v8/v9三轮全被它误导，连"目标关节
    回原点走到一半停"也是它：v9按假起点68.4°分2瓣，臂物理走到第1瓣~34°即被假校验
    中止）。真实关节角在偏移192（2026-10-09双帧扫描定位+示教器交叉证实）。
    本函数：发指令→等物理收尾→用192字段核验到位；驱动假报断连时同样等收尾后
    核验（不重发）。"""
    try:
        getattr(robot, method)(target)
    except StoppedError as exc:
        if str(exc).strip() != 'Robot not connected':
            raise
        # v14o 静默重连：假断连是本环境常态（每条 MoveJ 指令结束后都可能误报）；30004
        # 反馈通道独立于驱动连接，静止确认与重连并行进行，压缩跳间停顿税。
        # 护栏不变：未自然收尾（20s 上限）仍停、落点仍 0.5° 校验、重连失败仍停。
        log('驱动报断连——等待收尾与后台重连并行进行（不重发指令）…')
        import threading as _st
        reconnected = []
        def _bg_reconnect():
            for _retry in range(3):
                if ensure_connected():
                    reconnected.append(True)
                    return
                time.sleep(1.0)
        _rt = _st.Thread(target=_bg_reconnect, daemon=True, name='silent_reconnect')
        _rt.start()
        # v14u：到位等待下沉在断连分支（MovL 直发永远走本分支——v14s 教训）——
        # 目标锚定：距目标≤2°且静止=完成，不猜起步（速度判据已出局）。非 MovL
        # 直发（expect_target=None）退化为常规静止确认（20s 上限护栏不变）。
        actual, is_static = _wait_arrival_then_static(expect_target)
        if not is_static:
            raise RuntimeError('驱动报断连后等待%.0fs仍未静止，停止。' % 20.0) from exc
        err = max(abs(a - b) for a, b in zip(actual, target))
        if require_joints and err > MOVE_OFFSET_TOL:
            raise RuntimeError('断连收尾后未到位：目标%s，实测%s（误差%.2f°），停止待判读。'
                               % (['%.2f' % v for v in target], ['%.2f' % v for v in actual], err)) from exc
        _rt.join(timeout=4.0)
        if not reconnected:
            raise RuntimeError('已到位但驱动重连失败，停止后续指令。') from exc
        log('驱动断连但运动已自然完成到位；已重连驱动，继续。')
        return
    actual, is_static = _wait_controller_static()
    if not is_static:
        raise RuntimeError('指令返回后等待静止超时（20s），停止。')
    err = max(abs(a - b) for a, b in zip(actual, target))
    if require_joints and err > MOVE_OFFSET_TOL:
        raise RuntimeError('落点偏差%.2f°：目标%s，实测%s，停止待判读。'
                           % (err, ['%.2f' % v for v in target], ['%.2f' % v for v in actual]))
    return


MOVE_OFFSET_TOL = 0.5   # 到位容差（°）：反馈字段校正后，超过即停止待判读


# v13（方案B）：驱动 MOVL 执行层已判死（3 次实机断连指纹 + .pyc 反汇编直连无收尾），
# 所有 MoveL 执行全部替换为「细分途经点 + MoveJ」。作业面短段（≤ TRANSIT_DIRECT_MAX_MM）
# 用 MoveL 指令的 1mm 逆解采样出 ≤ LINEAR_SUBSTEP_MM 的途经关节序列，MoveJ 逐跳执行；
# 过渡段长段优先 MoveJ 直达（须过 TCP 偏离≤max_deviation 且整弧 MoveJ_Test 碰撞检查），
# 不满足才退回细分。预检层 MoveL_Test@1mm 保留：仍是「这一段能不能走直线」的权威筛选器。
TRANSIT_DIRECT_MAX_MM = 300.0   # 超过此段长的 TCP 段视为自由空间过渡段，尝试 MoveJ 直达
LINEAR_SUBSTEP_MM = 20.0        # 作业面细分步长：v14m(40mm) 实机碰撞实证弦误差可吃掉真裕度（轴线距199.9-半径180≈19.9mm），回 20mm 安全基准（v14k 两度全通过）；途经点弦误差 <0.5mm

MOVL_DIRECT_MAX_MM = 150.0   # v14p 法兰补偿MOVL 适用段长上限。★v14v 校正注释：实测 P5=100.0mm（成功，1.1s 到位）、P9=100.0mm（失败，60s 仍差 10.69°）
                             #   ⇒ 段长【不是】区分成败的变量；旧注释「P9≈80mm」已过时。v14v 起的兜底是「直发失败自动回退细分路径」，故本上限可维持 150
MOVL_FLANGE_TOL_MM = 8.0     # v14q 直发 MovL 法兰位置粗验收容差：控制器 MovL 固有落点残差实测 4.61mm（v14p 首航）/5.5mm（v14l）双样本，取实测+裕量；超此值=落点异常⇒v14v 起回退细分路径（不再停机）
MOVL_FLANGE_TOL_DEG = 1.0    # v14q 直发 MovL 法兰姿态粗验收容差（实测 0.616°+裕量）；通过后 MoveJ 微纠偏收口到关节级 0.5° 内
MOVL_ARRIVE_WAIT_S = 60.0    # v14u MovL 直发到位等待上限：目标锚定（距目标≤2°且静止即完成），不猜起步——v14t 10:38 实测 P9 起步延迟>6s；60s 为 10 倍裕量，每5s进度日志实测真实延迟。
                             #   ★v14v：超时不再终止任务，改为回退细分途经点路径重跑本段（10-13 11:05 P9 实测 60s 差 10.69° ⇒ 该点位不适用直发）
MOVL_ARRIVE_TOL_DEG = 2.0    # v14u 到位判定关节距离阈（°）：粗验收前哨——法兰级粗验收(≤8mm/≤1°)+MoveJ收口紧随其后罩终点；此处不走 MOVE_OFFSET_TOL=0.5°（require_joints=False 路径，护栏语义不降级）


def _movl_flange_accept(joints_now, joints_target):
    """v14q：直发 MovL 落点的法兰位姿级粗验收。

    v14p 首航实证：控制器 MovL 固有落点残差 ~5mm/0.6° 级（v14p 4.61mm/0.616°、v14l 5.5mm，
    双样本跨版本一致）——关节级 0.5° 判据会把正常落点误判为事故。改用法兰语义验收：
    FK(实测) vs FK(目标)，位置≤MOVL_FLANGE_TOL_MM 且姿态≤MOVL_FLANGE_TOL_DEG 即过；
    过后在 _execute_checked_real 里发一条 MoveJ 微纠偏收口（关节级 0.5° 校验罩住终点）。
    超容差=落点异常（构型翻转/卡住/送错目标），照旧抛 RuntimeError 即停待判读。"""
    _f_now = invH(robot.PoseFrame()) * robot.SolveFK(joints_now)      # 法兰位姿（无工具）
    _f_tgt = invH(robot.PoseFrame()) * robot.SolveFK(joints_target)
    _d = _f_now * invH(_f_tgt)
    _mm = norm(_d.Pos())
    _deg = math.degrees(pose_angle(_d))
    return _mm, _deg


def _movl_direct_ready():
    """v14p 法兰补偿MOVL 开关是否可用：GUI 变量已建（正常运行）才开；
    离线 verify 的 exec 命名空间里没有 real_movldirect_var（NameError），
    自动回 False——离线验证的计划/指纹与该开关无关（规划层零改动）。"""
    try:
        return isinstance(real_movldirect_var, tk.BooleanVar)
    except Exception:
        return False


MOVE_SEGMENT_MAX_DEG = 64.0  # 每瓣最大关节跨度：驱动约8秒无完成回报即断连，20°/s下64°≈3秒，留足裕量


J6_SPIN_SEGMENT_DEG = 60.0   # MoveL 纯J6自转段分瓣跨度（无平移时关节插值=笛卡尔路径）


def _is_pure_j6_spin(start, target):
    """MoveL 目标仅 J6 变化（J1~J5 不动）：关节插值与笛卡尔路径重合，可精确分瓣。"""
    return max(abs(a - b) for a, b in zip(start[:5], target[:5])) < 1e-6


def _move_with_completion_check(method, target, allow_split=True):
    """长运动分瓣执行（v9）：驱动对单条指令约8秒无完成回报就断连（本环境常态，
    test.py 同款假报，它每段部在几秒内完成所以从没撞上）；大跨度关节运动沿
    预检验证过的同一条关节直线剖成若干瓣，每瓣都在死线内完成，路径不变，
    仅增设停顿点。MoveL 纯J6自转段同理分瓣；带平移 MoveL 与小跨度段保持原样。"""
    if not allow_split:
        # v11: 单点运动/关节运动不分瓣，恢复一指令直达（到位校验与假断连容忍保留）
        _single_move_settle(method, target)
        return
    try:
        start = _live_joints()
        total = max(abs(float(b) - float(a)) for a, b in zip(start, target))
    except Exception:
        start, total = None, None
    if method == 'MoveJ' and total is not None and total > MOVE_SEGMENT_MAX_DEG:
        pieces = int(math.ceil(total / MOVE_SEGMENT_MAX_DEG))
        log('长运动分瓣：跨度%.1f° → %d 瓣执行（同一关节直线，仅增设停顿点）。' % (total, pieces))
        for k in range(1, pieces + 1):
            way = [a + (b - a) * k / pieces for a, b in zip(start, target)]
            _single_move_settle('MoveJ', way)
            _require_joints(way)  # 瓣间校验到位，也给驱动链路留出响应时间
        return
    if (method == 'MoveL' and total is not None and _is_pure_j6_spin(start, target)
            and total > J6_SPIN_SEGMENT_DEG):
        pieces = int(math.ceil(total / J6_SPIN_SEGMENT_DEG))
        log('J6自转分段：跨度%.1f° → %d 段MoveL（纯自转，路径与笛卡尔路径重合）。' % (total, pieces))
        for k in range(1, pieces + 1):
            way = [a + (b - a) * k / pieces for a, b in zip(start, target)]
            _single_move_settle('MoveL', way)
            _require_joints(way)
        return
    _single_move_settle(method, target)


_real_running = False  # 2026-10-09 补回：旧版 L510 有此初始化，升级版漏带导致点击即 NameError 静默炸裂


def _execute_checked_real(data, single_method=None):
    global _real_running
    log('【入口】_execute_checked_real：%d 点，single_method=%s' % (len(data) if data is not None else -1, single_method))
    if _real_running:
        log('已有实机任务正在执行。')
        return
    _real_running = True
    completed = 0
    movl_direct = False  # v14p：入口预置，防异常早于赋值时 except 块二次 NameError（v14l 教训）
    try:
        log('开始校验录入数据…')
        records = _validated_records(data)
        log('录入数据校验通过：%d 点。' % len(records))
        if single_method is None and len(records) > 1:
            expanded = _retreat_orientation_records(records)
            log('连续轨迹：%d个录入点展开为%d个执行点（含姿态退让）。' % (len(records), len(expanded)))
            records = expanded
        deviation = float(real_deviation_var.get())
        if not math.isfinite(deviation) or deviation < 0:
            raise ValueError('允许偏离必须为非负有限数。')
        log('偏离上限 %.1f mm，检查机器人连接…' % deviation)
        if not ensure_connected():
            return
        start = _live_joints()
        log('实机当前关节：%s' % ['%.2f' % v for v in start])
        # 长预检/运动期间 RoboDK 主程序忙或不消费驱动输出，驱动链路会饿死断开（15:20:56 P1 中途断连同因）。
        # 保活线程用独立 API 连接（避免被 MoveJ 阻塞主连接），每2秒一次 ConnectedState（只读），
        # 贯穿预检+执行全程，直到任务结束才停（v7 错在预检后就停，P1 运动中饿死驱动）。
        import threading as _th
        _keepalive_stop = _th.Event()
        def _driver_keepalive():
            n = 0
            _ka_rdk = Robolink()
            _ka_robot = _ka_rdk.Item('', ITEM_TYPE_ROBOT)
            while not _keepalive_stop.wait(2.0):
                n += 1
                try:
                    s, _m = _ka_robot.ConnectedState()
                    if s < 0:
                        log('【保活】第%d次发现驱动掉线（%s），已请求重连。' % (n, _m))
                        _ka_robot.Connect()
                except Exception:
                    pass  # 主程序忙时 API 调用可能慢/超时，下一轮再试
        _ka_thread = _th.Thread(target=_driver_keepalive, daemon=True, name='driver_keepalive')
        _ka_thread.start()
        log('已启驱动保活（贯穿预检+执行）。')
        frame, tool = robot.PoseFrame(), robot.PoseTool()
        log('开始台子/地面避障预检，尚未发送运动指令。')
        plan = _prepare_real_plan(records, start, deviation, single_method)
        # 保活线程不在此处停：执行阶段同样需要（v7 教训）
        # 预检后复核：驱动必须就绪且关节与预检起始一致，否则取消。
        if not ensure_connected():
            log('预检后驱动断连，重连未成功，取消执行。')
            return
        _require_joints(start)
        log('预检后连接复核通过，准备发运动指令。')
        for before, after in ((frame, robot.PoseFrame()), (tool, robot.PoseTool())):
            error = invH(before)*after
            if norm(error.Pos()) > 0.01 or pose_angle(error) > math.radians(0.01):
                raise RuntimeError('预检期间工具或参考坐标系改变，取消执行。')
        robot.setSpeed(ROBOT_SPEED)
        RDK.Command('Trace','Reset')
        RDK.Command('Trace','On')
        expected = start
        # v14k：停用长运动分瓣（split_moves 恒 False）。2026-10-12 实测日志坐实：假断连与跨度无关，
        # 60°/95°/169°/180° 的瓣与 20mm 途经点每条指令都在断，分瓣已不防任何东西，只剩每瓣一轮
        # 等待+重连停顿税；_single_move_settle 断连容忍（_wait_controller_static 20s 静止上限）
        # 罩得住单条长指令的收尾（20°/s 下 180°≈9s<20s）。分瓣机制与常量原样留档，遇真断连指纹
        # （未自然收尾/未到位）随时把本行改回 single_method is None and len(records) > 1 即可恢复。
        split_moves = False
        movl_direct = bool(real_movldirect_var.get()) if _movl_direct_ready() else False
        if movl_direct:
            log('【v14u】法兰补偿MOVL开启：短直线段（≤%.0fmm、姿态恒定≤0.5°）一指令直发驱动 MOVL（工具补偿；落点法兰级粗验收≤%.0fmm/%.1f°+MoveJ微纠偏收口+到位等待≤%.0fs 目标锚定；规划与预检不变；断连指纹照旧即停，去勾即回细分路径）。' % (MOVL_DIRECT_MAX_MM, MOVL_FLANGE_TOL_MM, MOVL_FLANGE_TOL_DEG, MOVL_ARRIVE_WAIT_S))
        for i, step in enumerate(plan, 1):
            for rewind in step['rewinds']:
                _require_joints(expected)
                _move_with_completion_check("MoveJ", rewind, split_moves)
                _require_joints(rewind)
                expected = rewind
            _require_joints(expected)
            waypoints = step.get('waypoints') or []
            if step['method'] == 'MoveL' and not waypoints:
                # 理论不可达：v13 起所有 MoveL 步都带细分途经点；不带则说明规划层契约被破坏
                raise RuntimeError(f"P{i}：MoveL 步缺少细分途经点，拒绝发送驱动 MOVL（已判死）。")
            seg_mm = seg_rot = None
            if movl_direct and step['method'] == 'MoveL' and waypoints:
                # 仅开关开启时才算（两次 FK 的 API 往返）；开关关/离线 verify 零开销
                _seg_rel = _trajectory_pose(step['joints']) * invH(_trajectory_pose(expected))
                seg_mm, seg_rot = norm(_seg_rel.Pos()), pose_angle(_seg_rel)
            _direct_done = False
            if (movl_direct and seg_mm is not None
                    and seg_mm <= MOVL_DIRECT_MAX_MM and seg_rot <= math.radians(0.5)):
                # v14p 法兰补偿MOVL：驱动 MOVL 无工具补偿、按法兰执行（v14l 11:30 实证停点法兰=
                # 命令TCP目标，差仅5.5mm）——将错就错：发送瞬间站内工具置单位变换，RoboDK
                # MoveL(joints) 换算出的笛卡尔目标即 FK(joints)=法兰目标位姿，控制器把法兰精确
                # 送到本步构型的法兰位姿，物理工具尖端（159.63mm）随之落在认证直线上。姿态恒定段
                # 法兰线=TCP线平移常向量，扫掠包络与细分路径一致；途经点保留在计划里（去勾即回
                # 同一条几何路径）；工具恢复放 finally，异常也不残留站内状态。
                # ★ v14u-fix（2026-10-13）：直发【失败时自动回退细分路径】，不再直接抛错停机——
                #   依据 10-13 11:05 实测：P9 直发 60s 仍距目标 10.69°（速度≈0），而 P5 同类直发
                #   1.1s 即到位；说明"法兰补偿直发"对某些点位（P9）根本走不到，属该优化本身的
                #   适用性边界，而不是任务失败。细分途经点路径是已验证的可靠路径（几何不变），
                #   故此处降级重跑，任务继续。
                log(f"P{i}：v14u 法兰补偿MOVL：段长{seg_mm:.1f}mm（姿态变化{math.degrees(seg_rot):.2f}°），收起 {len(waypoints)} 个细分途经点，一指令直发（工具临时置单位变换）。")
                _saved_tool_pose = robot.PoseTool()
                try:
                    robot.setPoseTool(eye(4))
                    # v14r：require_joints=False——假断连分支的关节级 0.5° 校验让位给下方
                    # 法兰级粗验收+MoveJ 微纠偏收口（终点仍回认证构型，护栏语义不降级）。
                    # v14u：expect_target=段目标关节——目标锚定到位等待（v14t 10:38 实测
                    # P9 起步延迟>6s 且指令事后自行执行完；不再猜「起步了没」，等「到
                    # 没到」：距目标≤2°且静止即完成，上限 60s，每5s进度日志）。
                    _single_move_settle('MoveL', step['joints'], require_joints=False,
                                        expect_target=step['joints'])
                    # v14q：MovL 落点法兰级粗验收（≤8mm/≤1°）+ MoveJ 微纠偏收口（关节级 0.5° 罩终点）。
                    # v14p 首航停在 0.95° 关节残差（法兰 4.61mm/0.616°）被 0.5° 护栏拦停——那是控制器
                    # MovL 固有落点残差（v14l 5.5mm 双样本背书），不是构型错误；但终点必须回到认证构型，
                    # 故验收通过后用一条短 MoveJ（~1° 关节差）收口，走 _single_move_settle 全套护栏。
                    _actual, _is_static = _wait_controller_static(samples=3, interval=0.2)
                    _mm, _deg = _movl_flange_accept(_actual, step['joints'])
                    if _mm > MOVL_FLANGE_TOL_MM or _deg > MOVL_FLANGE_TOL_DEG:
                        raise RuntimeError('v14u 法兰级粗验收未过：停点法兰残差%.2fmm/%.2f°（容差%.1fmm/%.1f°），实测关节%s，停止待判读。'
                                           % (_mm, _deg, MOVL_FLANGE_TOL_MM, MOVL_FLANGE_TOL_DEG,
                                              ['%.2f' % v for v in _actual]))
                    _jm = max(abs(a - b) for a, b in zip(_actual, step['joints']))
                    if _jm > MOVE_OFFSET_TOL:
                        log(f"P{i}：v14u MovL 直发落点法兰级验收通过（残差{_mm:.2f}mm/{_deg:.2f}°），关节残差{_jm:.2f}°——发 MoveJ 微纠偏收口。")
                        _single_move_settle('MoveJ', step['joints'])
                    _require_joints(step['joints'])
                    _direct_done = True
                except Exception as _direct_exc:
                    # ★ v14u-fix：直发失败不终止任务，改为回退细分途经点路径重跑本段
                    log(f"P{i}：【v14u-fix】法兰补偿MOVL直发未成功（{type(_direct_exc).__name__}: {_direct_exc}）"
                        f"⇒ 自动回退到【细分途经点路径】重跑本段（几何路径不变，工具已复原）。")
                finally:
                    robot.setPoseTool(_saved_tool_pose)
            if not _direct_done and waypoints:
                log(f"P{i}：执行预检方案 {step['method']}→MoveJ 细分，{len(waypoints)} 个途经点，终点关节={step['joints']}")
                for k, way in enumerate(waypoints, 1):
                    _move_with_completion_check('MoveJ', way, False)
                    _require_joints(way)
                _require_joints(step['joints'])
            elif not _direct_done:
                log(f"P{i}：执行预检方案 {step['method']}，关节={step['joints']}")
                _move_with_completion_check(step['method'], step['joints'], split_moves)
                _require_joints(step['joints'])
            expected = step['joints']
            completed += 1
        log(f'实机执行完成：{completed}/{len(plan)}点。')
    except Exception as exc:
        log(f'实机任务停止，已完成{completed}点：{type(exc).__name__}: {exc}')
        if movl_direct and ('断连' in str(exc) or '未到位' in str(exc) or '落点偏差' in str(exc) or '粗验收' in str(exc)):
            log('【v14v 提示】直发段的这类异常本应已在段内被捕获并自动回退细分路径；若仍走到这里，'
                '说明【细分路径本身】也失败了，请检查机械臂状态与报警（不再是"直发适用性"问题）。')
        try:
            actual, velocity, mode = _controller_feedback()
            log('停止时控制器实际反馈：关节=%s，速度=%s，模式=%s；不自动重发运动。' % (actual, velocity, mode))
        except Exception as feedback_error:
            log('停止时也无法取得控制器反馈：%s' % feedback_error)
    finally:
        _real_running = False
        try:
            _keepalive_stop.set()
            _ka_thread.join(timeout=3)
        except Exception:
            pass


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

    log("开始检查 MoveJ 兜底轨迹：%d 个采样点，允许最大TCP偏离 %.3f mm" % (samples + 1, max_deviation_mm))
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
            log("✕ MoveJ兜底轨迹拒绝：第 %d/%d 个采样点偏离TCP直线 %.3f mm > %.3f mm" %
                (k+1, samples+1, dev, max_deviation_mm))
            log("  t=%.3f  TCP=(%.3f, %.3f, %.3f)" % (t, p[0], p[1], p[2]))
            log("  因此不会执行这个MoveJ兜底动作，避免出现不可接受的大绕圈。")
            return False

    if max_info is not None:
        k, t, q, p = max_info
        log("✓ MoveJ兜底轨迹检查通过")
        log("  最大TCP偏离直线：%.3f mm（采样 %d/%d，t=%.3f）" % (max_dev, k+1, samples+1, t))
        log("  最大偏离点TCP=(%.3f, %.3f, %.3f)" % (p[0], p[1], p[2]))
    return True


# ============================================================
# 执行连续运动（MoveL失败时先检查MoveJ轨迹）
# ============================================================
def _collision_details():
    pairs = RDK.CollisionPairs()
    return '；'.join(f'{a.Name()}[连杆{ia}] 与 {b.Name()}[连杆{ib}]'
                    for a, b, ia, ib in pairs) or '路径碰撞或关节不可行'


def _enable_obstacle_checks():
    if RDK.RunMode() != RUNMODE_SIMULATE:
        raise RuntimeError('障碍物预检仅允许在仿真模式执行。')
    # 每次进入预检都清空预检缓存：缓存生命周期 = 单次预检规划，
    # 障碍物/工作站状态的变化在下一次预检即时生效。
    _plan_cache.clear()
    for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40'):
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
    RDK.setCollisionActive(COLLISION_ON)


def _check_single_joint_path(end):
    _enable_obstacle_checks()
    saved = robot.Joints().list()[:6]
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
    program = RDK.AddProgram('_TCP仿真_路径预检', robot)
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
            raise RuntimeError('路径预检返回的终点不匹配目标TCP。')
        return end, message
    finally:
        program.Delete()


def _linear_waypoints(start, target, step_mm=None):
    """v13：从一条 MoveL 指令采样细分途经关节点（按 IK 顺序，无分支翻转）。

    用 InstructionListJoints(mm_step=LINEAR_SUBSTEP_MM, collision_check=COLLISION_OFF) 采样：
    途经点与 MoveL 执行的是同一条几何直线，且 IK 连续选解（避免用全局 SolveIK 时
    途经点在多解间跳变）。碰撞已由 _linear_path_endpoint 的 MoveL_Test@1mm 权威判定，
    此处不再重复。返回含终点的关节点列表；空列表表示采样失败（调用方回退直达）。"""
    if step_mm is None:
        step_mm = LINEAR_SUBSTEP_MM
    key = ('waypoints', _cache_key_joints(start), _cache_key_pose(target), round(float(step_mm), 3))
    if key in _plan_cache:
        return [q[:] for q in _plan_cache[key]]
    program = RDK.AddProgram('_TCP仿真_细分采样', robot)
    saved = robot.Joints().list()[:6]
    try:
        program.setVisible(False)
        robot.setJoints(start)
        program.setPoseFrame(robot.PoseFrame())
        program.setPoseTool(robot.PoseTool())
        program.MoveJ(start)
        program.MoveL(target)
        message, matrix, status = program.InstructionListJoints(mm_step=step_mm, deg_step=1, collision_check=COLLISION_OFF)
        cols = matrix.tr().rows if matrix is not None else []
        if status < 0 or not cols:
            return []
        # 丢弃比步长更密的重复点（InstructionListJoints 在奇异附近会加密采样）
        picked = [list(map(float, cols[0][:6]))]
        for row in cols[1:]:
            q = list(map(float, row[:6]))
            if max(abs(a - b) for a, b in zip(q, picked[-1])) >= step_mm / 10.0:
                picked.append(q)
        # 去尾：InstructionListJoints 可能带比目标多一点的收尾点，以关节距离最近的为准
        end_q, _ = _linear_path_endpoint(start, target)
        if end_q is not None and picked and max(abs(a - b) for a, b in zip(end_q, picked[-1])) > 1.0:
            picked[-1] = list(map(float, end_q))
        _plan_cache[key] = [q[:] for q in picked]
        return [q[:] for q in picked]
    finally:
        program.Delete()
        robot.setJoints(saved)


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
    # v14-P2P：不再用 seed 候选/肘高排序，直接取离当前关节最近的逆解做逐级检查；
    # 最近解过不了偏离/碰撞时仍会在这里报错（单点 MoveJ 兜底路径保持可用）。
    lower, upper, _ = robot.JointLimits()
    candidates = [_nearest_ik_from_current(start, fanuc_to_pose(*values))]
    saved = robot.Joints().list()[:6]
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
    program = RDK.AddProgram('_TCP仿真_整段碰撞复核', robot)
    saved = robot.Joints().list()[:6]
    try:
        program.setVisible(False)
        program.setPoseFrame(robot.PoseFrame())
        program.setPoseTool(robot.PoseTool())
        program.MoveJ(start)
        for step in plan:
            for q in step['rewinds']:
                program.MoveJ(q)
            if step['method'] == 'MoveL' and not step.get('waypoints'):
                # v13 防呆：MoveL 步必须带细分途经点，否则规划层契约被破坏
                raise ValueError('整段碰撞复核：MoveL 步缺少细分途经点，拒绝。')
            getattr(program, step['method'])(step['joints'])
        message, matrix, status = program.InstructionListJoints(
            mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        if status < 0 or 'collision' in message.lower():
            raise ValueError('整段碰撞复核未通过：' + message)
    finally:
        program.Delete()
        robot.setJoints(saved)


def _ik_branch_candidates(target_pose, reference):
    """v14c：某个 TCP 位姿的全部限位内 IK 分支（含 J6 圈数取近表示），
    与 _nearest_ik_from_current 同款筛选规则。"""
    solutions = robot.SolveIK_All(_tcp_target_to_flange(target_pose))
    lower, upper, _ = robot.JointLimits()
    lower, upper = lower.list(), upper.list()
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
    for q in candidates[:]:
        nearest = [min((v + 360*k for k in range(math.ceil((lower[j]-v)/360),
                       math.floor((upper[j]-v)/360)+1)), key=lambda a: abs(a-reference[j]))
                   for j, v in enumerate(q)]
        if not any(max(abs(a-b) for a, b in zip(nearest, old)) < 1e-6 for old in candidates):
            candidates.append(nearest)
    return candidates


def _nearest_ik_from_current_lookahead(current_q, target_pose, lookahead_ok):
    """v14i：同 _nearest_ik_from_current，但要求选出的解能满足前视条件 lookahead_ok(cand)->bool；
    没有满足者时退回最近解（死路由后续救援链/种子重试兜底）。"""
    candidates = _ik_branch_candidates(target_pose, current_q)
    if not candidates:
        raise ValueError('没有限位内的逆解。')
    ranked = sorted(candidates, key=lambda q: sum((q[j]-current_q[j])**2 for j in range(6)))
    for cand in ranked:
        if lookahead_ok(cand):
            return cand[:]
    return ranked[0][:]


def _nearest_ik_from_current(current_q, target_pose):
    """v14-P2P：从全部逆解中选离当前关节角最近的解（含 J6 圈数取近）。

    与 test.py 的肘高排序不同：以【关节空间离当前构型最近】为准，相邻点之间不会突变构型。
    没有限位内解时抛 ValueError。"""
    solutions = robot.SolveIK_All(_tcp_target_to_flange(target_pose))
    lower, upper, _ = robot.JointLimits()
    lower, upper = lower.list(), upper.list()
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
    # 同一姿态再补一圈数取近的表示，避免强制归零导致大绕行。
    for q in candidates[:]:
        nearest = [min((v + 360*k for k in range(math.ceil((lower[j]-v)/360),
                       math.floor((upper[j]-v)/360)+1)), key=lambda a: abs(a-current_q[j]))
                   for j, v in enumerate(q)]
        if not any(max(abs(a-b) for a, b in zip(nearest, old)) < 1e-6 for old in candidates):
            candidates.append(nearest)
    if not candidates:
        raise ValueError('没有限位内的逆解。')
    return min(candidates, key=lambda q: sum((q[j]-current_q[j])**2 for j in range(6)))[:]


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
    """v14c：首点全分支种子枚举 + 整段重试。

    贪心最近解在换向步（如轨迹7 P6 的原地转 90°→180°）会把 wrist 构型选到贴圆柱，
    后续任何分支都碰；TCP仿真宏靠首点种子枚举+整段重试避开这类死路。v14c 移植该机制：
    种子按肘高排序优先，贪心只负责段内选解；某段死路（含 MoveL 兑底都失败）
    则整段换种子重试，全部种子失败才报错。"""
    _enable_obstacle_checks()
    if not math.isfinite(max_deviation) or max_deviation < 0:
        raise ValueError('MoveJ允许偏离必须是非负有限数。')
    for i, rec in enumerate(records):
        vals = rec['values']
        if rec['type'] not in ('TCP', 'JOINT') or len(vals) != 6 or not all(math.isfinite(v) for v in vals):
            raise ValueError(f'P{i+1}：点类型或六维数值无效。')
        if rec.get('singular', False):
            # v14a：恢复 v13 同款奇异点规则校验（P2P 规划层支持奇异点步）
            if rec['type'] != 'TCP' or i == 0 or records[i-1]['type'] != 'TCP' or records[i-1].get('singular', False):
                raise ValueError(f'P{i+1}：特异点必须紧跟普通TCP点。')
            if rec.get('spin360', False):
                if rec.get('j6_delta', 360) not in (-360, 360):
                    raise ValueError(f'P{i+1}：J6自转方向必须为+360或-360。')
                if max(abs(a - b) for a, b in zip(rec['values'], records[i-1]['values'])) > 1e-3:
                    raise ValueError(f'P{i+1}：J6自转360°特异点的六维数值必须与前一个TCP点完全相同。')
            elif rec.get('j6_delta', 180) not in (-180, 180):
                raise ValueError(f'P{i+1}：J6方向必须为+180或-180。')
    saved = robot.Joints().list()[:6]
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
    try:
        RDK.Render(False)
        # v14c：首点全分支种子枚举（肘高优先），某种子整段死路时换构型重试。
        first_tcp = next((r for r in records if r['type'] == 'TCP' and not r.get('singular', False)), None)
        if first_tcp is not None:
            seeds = _ik_branch_candidates(fanuc_values_to_pose(*first_tcp['values']), saved)
            seeds = [s for s in seeds if _movej_test_cached(saved, s, 1) == 0] or seeds
            seeds.sort(key=lambda s: _obstacle_posture_key(s, saved))
        else:
            seeds = [None]
        for seed_rank, seed in enumerate(seeds, 1):
            if len(seeds) > 1:
                log(f'—— 尝试首点分支种子 {seed_rank}/{len(seeds)}：' +
                    ('%s' % [round(v, 1) for v in seed] if seed else '无种子(关节轨迹)'))
            q = saved[:]
            plan = []
            try:
                seed_used = seed is None
                for i, rec in enumerate(records, 1):
                    rewinds = []
                    delta = None
                    method, fallback, waypoints = 'MoveJ', False, []
                    lookahead_ok = None  # v14j：循环顶初始化（首个TCP点走种子路径时前视绑定也可安全引用）
                    if rec['type'] == 'JOINT':
                        end = [float(v) for v in rec['values'][:6]]
                        note = '录入关节直达'
                    elif rec.get('singular', False):
                        # v14a：奇异点步——只转 J6（±180 换向 / ±360 自转）。
                        # ±180：从当前解纯转 J6，由下方 FK 校验把关；超限时先试反方向（终点位姿不变）再试整圈回绕。
                        target = fanuc_values_to_pose(*rec['values'])
                        delta = rec.get('j6_delta', 180)

                        def _fk_matches(candidate):
                            error_pose = invH(target) * _trajectory_pose(candidate)
                            return norm(error_pose.Pos()) <= 1e-3 and pose_angle(error_pose) <= math.radians(.01)

                        end = q[:]
                        end[5] += delta
                        if not lower[5] <= end[5] <= upper[5]:
                            alt = q[:]
                            alt[5] -= delta
                            if lower[5] <= alt[5] <= upper[5]:
                                log(f'P{i}：J6 {delta:+d}°超限，改用反方向 {-delta:+d}°（终点位姿不变）。')
                                end, delta = alt, -delta
                            if not lower[5] <= end[5] <= upper[5]:
                                for rewound in _checked_j6_rewinds(q, lower, upper, max_deviation):
                                    if lower[5] <= rewound[5] + delta <= upper[5]:
                                        rewinds.append(rewound[:])
                                        q = rewound
                                        end = q[:]
                                        end[5] += delta
                                        break
                                else:
                                    raise ValueError(f'P{i}：J6 {delta:+d}°超限：反方向与整圈回绕均不可行。')
                        if not _fk_matches(end):
                            raise ValueError(f'P{i}：仅旋转J6无法到达所标注TCP，请检查特异点标记/工具。')
                        # v14d：换向步碰撞时，先试反方向（终点位姿不变），再试整圈回绕——
                        # TCP仿真靠方向枚举能避开这类碰撞，P2P 此前只在超限时才换向。
                        # v14j：反方向终点=当前解−delta（旧代码误算 q−2δ，朝向未翻转、FK 必不匹配，
                        # 15/15 种子全死于此——probe_p14_lookahead.py 坐实）。
                        if _movej_test_cached(q, end, 1) != 0:
                            alt = q[:]
                            alt[5] -= delta
                            flipped = False
                            if lower[5] <= alt[5] <= upper[5] and _fk_matches(alt) and _movej_test_cached(q, alt, 1) == 0:
                                log(f'P{i}：J6 {delta:+d}°扫过障碍，改用反方向 {-delta:+d}°（终点位姿不变）。')
                                end, delta, flipped = alt, -delta, True
                            if not flipped:
                                for rewound in _checked_j6_rewinds(q, lower, upper, max_deviation):
                                    cand = rewound[:]
                                    cand[5] += delta
                                    if lower[5] <= cand[5] <= upper[5] and _fk_matches(cand) and _movej_test_cached(q, cand, 1) == 0:
                                        log(f'P{i}：J6 {delta:+d}°两方向均碰，先整圈回绕再换向。')
                                        rewinds.append(rewound[:])
                                        q, end, flipped = rewound, cand, True
                                        break
                            if not flipped:
                                # v14f：两方向都碰——先切到同位姿的其他 IK 分支（碰撞预检过），
                                # 从那里再换向；途经的构型跳记入 rewinds 由执行层逐跳执行。
                                # v14j：枚举基准改为当前（未翻转）位姿——旧代码误用翻转后 target，
                                # 候选再 ±180 回到未翻转位姿，FK 对 target 永不匹配，结构性必死。
                                for cand in sorted(_ik_branch_candidates(_trajectory_pose(q), q),
                                                   key=lambda c: sum((c[j]-q[j])**2 for j in range(6))):
                                    for sgn in (delta, -delta):
                                        after = cand[:]
                                        after[5] += sgn
                                        if not (lower[5] <= after[5] <= upper[5] and _fk_matches(after)):
                                            continue
                                        if _movej_test_cached(q, cand, 1) == 0 and _movej_test_cached(cand, after, 1) == 0:
                                            log(f'P{i}：J6 ±180°两方向均碰，先切IK分支再换向（rewinds 跳转）。')
                                            rewinds.append(cand[:])
                                            q, end, delta, flipped = cand, after, sgn, True
                                            break
                                    if flipped:
                                        break
                            if not flipped:
                                # v14g：同位姿先 MoveL 到场再换向——MoveL 连续选解给出的构型
                                # 正是 TCP仿真 实测可换向的构型（贪心最近解构型两方向都扫障碍）。
                                lin_end, lin_detail = _linear_path_endpoint(q, target)
                                if lin_end is not None:
                                    pre_waypoints = _linear_waypoints(q, target)
                                    if pre_waypoints:
                                        for sgn in (delta, -delta):
                                            after = lin_end[:]
                                            after[5] += sgn
                                            if not (lower[5] <= after[5] <= upper[5] and _fk_matches(after)):
                                                continue
                                            if _movej_test_cached(lin_end, after, 1) == 0:
                                                log(f'P{i}：J6 两方向均碰，先 MoveL 到场（连续选解构型）再{sgn:+d}°换向。')
                                                plan.append(dict(method='MoveL', joints=lin_end[:], special=False,
                                                                 fallback=False, rewinds=[], j6_delta=None,
                                                                 waypoints=pre_waypoints, p2p_note='换向前MoveL到场'))
                                                q, end, delta, flipped = lin_end[:], after, sgn, True
                                                break
                            if not flipped:
                                raise ValueError(f'P{i}：J6 ±180°换向两方向均碰撞（含回绕/分支/MoveL到场尝试），该构型不可行。')
                        note = ('J6自转%+d°' % delta) if rec.get('spin360', False) else ('J6换向%+d°' % delta)
                    else:
                        target = fanuc_values_to_pose(*rec['values'])
                        # v14h：与前一点同位姿（停顿点，如轨迹7 P7）——不重新选解，
                        # 保持当前构型不动，只往计划里记一个停顿点。
                        if max(abs(_trajectory_pose(q).Pos()[j] - target.Pos()[j]) for j in range(3)) < 1e-3 and \
                           pose_angle(invH(target) * _trajectory_pose(q)) < math.radians(.01):
                            plan.append(dict(method='MoveJ', joints=q[:], special=False, fallback=False,
                                             rewinds=[], j6_delta=None, waypoints=[], p2p_note='同位姿停顿'))
                            continue
                        if not seed_used:
                            end = seed[:]  # v14c：首个TCP点直接采用种子分支（离起点可达性已在种子筛选时验证）
                            seed_used = True
                        else:
                            # v14i：前视——下一个执行点是 ±180 换向时，本点选解必须能完成那次换向
                            #（两方向任一可通行），否则贪心构型会把换向逼成死路。
                            nxt = records[i] if i < len(records) else None
                            lookahead_ok = None
                            if nxt is not None and nxt.get('singular', False) and not nxt.get('spin360', False):
                                nxt_values = nxt['values']
                                def lookahead_ok(cand, _vals=nxt_values, _lower=lower, _upper=upper):
                                    nxt_target = fanuc_values_to_pose(*_vals)
                                    for sgn in (180, -180):
                                        after = cand[:]
                                        after[5] += sgn
                                        if not (_lower[5] <= after[5] <= _upper[5]):
                                            continue
                                        err = invH(nxt_target) * _trajectory_pose(after)
                                        if norm(err.Pos()) > 1e-3 or pose_angle(err) > math.radians(.01):
                                            continue
                                        if _movej_test_cached(cand, after, 1) == 0:
                                            return True
                                    return False
                                log(f'P{i}：前视模式（P{i+1}为±180换向，选解需兼顾换向可行性）。')
                            end = (_nearest_ik_from_current_lookahead(q, target, lookahead_ok)
                                   if lookahead_ok else _nearest_ik_from_current(q, target))
                        note = 'TCP最近解直达'
                        # v14j：前视绑定执行——本点是换向前夜：前视选出的构型若弧碰，不得退 MoveL
                        # （连续选解会静默锁回当前族，把死局推迟到换向步才爆——种子13 实证），
                        # 也不得由 v14c 救援收无前视资格的分支；只能换用其他前视合格分支直达，
                        # 全部失败则本构型判死、整段换种子重试。
                        bound_applied = False
                        if lookahead_ok is not None and _movej_test_cached(q, end, 1) != 0:
                            detail_bound = _collision_details()
                            bound = None
                            for cand in sorted(_ik_branch_candidates(target, q),
                                               key=lambda c: sum((c[j]-q[j])**2 for j in range(6))):
                                if lookahead_ok(cand) and _movej_test_cached(q, cand, 1) == 0:
                                    bound = cand
                                    break
                            if bound is not None:
                                end, note, bound_applied = bound[:], '前视绑定避障直达', True
                                log(f'P{i}：前视构型弧碰（{detail_bound}），改用另一前视合格分支直达（前视绑定）。')
                            else:
                                raise ValueError(f'P{i}：MoveJ弧碰撞（{detail_bound}），其余前视合格分支均不可通行；'
                                                 '拒绝退 MoveL（连续选解会丢前视资格），本构型判死。')
                        # v14b：MoveJ 直达弧碰撞时，退回 v13 验证过的 MoveL 直线细分执行。
                        if not bound_applied and _movej_test_cached(q, end, 1) != 0:
                            detail = _collision_details()
                            lin_end, lin_detail = _linear_path_endpoint(q, target)
                            if lin_end is None:
                                # v14c：直线也碰——枚举该目标全部 IK 分支找可通行 MoveJ（换构型救援）
                                rescued = None
                                for cand in sorted(_ik_branch_candidates(target, q),
                                                   key=lambda c: sum((c[j]-q[j])**2 for j in range(6))):
                                    if _movej_test_cached(q, cand, 1) == 0:
                                        rescued = cand
                                        break
                                if rescued is None:
                                    raise ValueError(f'P{i}：MoveJ弧碰撞（{detail}），且MoveL直线也失败：{lin_detail}；'
                                                     '该目标全部IK分支均不可通行。')
                                end, note = rescued[:], 'IK分支救援直达'
                                log(f'P{i}：最近解与直线均碰，切换IK分支救援成功。')
                            else:
                                waypoints = _linear_waypoints(q, target)
                                if not waypoints:
                                    raise ValueError(f'P{i}：MoveJ弧碰撞（{detail}），MoveL细分采样失败，拒绝。')
                                end, method, fallback = lin_end, 'MoveL', True
                                note = 'MoveJ弧碰退回MoveL细分'
                                log(f'P{i}：MoveJ弧碰撞（{detail}），改走 MoveL 直线细分（{len(waypoints)} 途经点）。')
                    if not all(lower[j] <= end[j] <= upper[j] for j in range(6)):
                        raise ValueError(f'P{i}：关节超限，J6目标={end[5]:.3f}°。')
                    if method == 'MoveJ' and _movej_test_cached(q, end, 1) != 0:
                        # v14e：普通TCP点最后一级救援——v13 遗产 _obstacle_joint_target
                        # （21候选、肘高排序、限TCP偏离）选避障构型，TCP仿真靠它在同一站过关。
                        try:
                            end = _obstacle_joint_target(q, rec['values'], max_deviation, log)
                            note = '避障选解直达'
                        except ValueError:
                            raise ValueError(f'P{i}：MoveJ路径检查失败（含避障选解）：' + _collision_details())
                        if _movej_test_cached(q, end, 1) != 0:
                            raise ValueError(f'P{i}：MoveJ路径检查失败：' + _collision_details())
                    plan.append(dict(method=method, joints=end[:], special=rec.get('singular', False), fallback=False,
                                     rewinds=rewinds, j6_delta=delta,
                                     waypoints=waypoints, p2p_note=note))
                    q = end[:]
                _verify_obstacle_plan(saved, plan)
                log(f'P2P+奇异点整段路径预检通过：{len(plan)}点。')
                return plan
            except ValueError as exc:
                if seed_rank >= len(seeds):
                    raise
                log(f'种子 {seed_rank}/{len(seeds)} 在此构型失败（{exc}），换下一构型整段重试…')
    finally:
        robot.setJoints(saved)
        RDK.Render(True)

root = tk.Tk()
root.title("RoboDK - 机械臂运动控制（P2P v14u）")
root.geometry("1200x750")
root.resizable(True, True)

tk.Label(root, text="Dobot CR5 运动控制", font=("Microsoft YaHei", 16, "bold")).pack(pady=10)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# ---- 选项卡 1：单点运动 ----
tab_single = ttk.Frame(notebook)
notebook.add(tab_single, text="单点运动")

frame_coord = tk.LabelFrame(tab_single, text="目标 TCP（Fanuc 格式）")
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

tk.Button(btn_single_frame, text="读取当前 TCP", command=_read_current, width=15).pack(side=tk.LEFT, padx=3)
tk.Button(btn_single_frame, text="当前 TCP -> 输入框", command=_fill_current, width=20).pack(side=tk.LEFT, padx=3)
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
         text="输入 J1~J6 目标角度（deg）；完整关节路径预检通过后才发送实机 MoveJ。",
         fg="#555555").pack(anchor=tk.W, padx=15, pady=5)
tk.Label(tab_joint,
         text="安全提示：首次测试建议只改变一个关节、改变 5~10°，确认方向和角度定义正确后再进行大角度运动。",
         fg="#C62828").pack(anchor=tk.W, padx=15, pady=2)

# ---- 选项卡 3：连续运动 ----
tab_traj = ttk.Frame(notebook)
notebook.add(tab_traj, text="连续运动")

frame_traj_input = tk.LabelFrame(
    tab_traj,
    text="连续运动点输入：每次输入 1 个 TCP 点或 1 组关节角度，点击“检查并加入”"
)
frame_traj_input.pack(fill=tk.X, padx=10, pady=10)

type_frame = tk.Frame(frame_traj_input)
type_frame.pack(fill=tk.X, padx=8, pady=5)

tk.Label(type_frame, text="点类型：").pack(side=tk.LEFT, padx=3)

traj_type = tk.StringVar(value="TCP")
tk.Radiobutton(
    type_frame, text="TCP（X,Y,Z,Rx,Ry,Rz）",
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
    text="末端特异点（跳过IK，仅J6转动）",
    variable=singular_var
).pack(side=tk.LEFT, padx=3)

tk.Label(singular_frame, text="J6方向：").pack(side=tk.LEFT, padx=(15, 3))
tk.Radiobutton(singular_frame, text="+180°", variable=j6_direction_var, value=180).pack(side=tk.LEFT, padx=3)
tk.Radiobutton(singular_frame, text="-180°", variable=j6_direction_var, value=-180).pack(side=tk.LEFT, padx=3)
spin_var = tk.BooleanVar(value=False)
tk.Checkbutton(singular_frame, text="J6自转360°（第二类，六维与前点相同）", variable=spin_var).pack(side=tk.LEFT, padx=3)

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
    type_frame, text="TCP（X,Y,Z,Rx,Ry,Rz）",
    variable=traj_type, value="TCP",
    command=_update_traj_labels_and_defaults
).pack_forget()

# 重新建立带 command 的两个单选按钮
for widget in list(type_frame.pack_slaves()):
    if isinstance(widget, tk.Radiobutton):
        widget.destroy()

tk.Radiobutton(
    type_frame, text="TCP（X,Y,Z,Rx,Ry,Rz）",
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
    text="读取当前TCP并写入",
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
    text="加入点时检查格式并保留关节圈数；执行前再进行整段限位、台子和地面碰撞检查。",
    fg="#555555"
).pack(anchor=tk.W, padx=15, pady=3)

frame_record = tk.LabelFrame(
    tab_traj,
    text="已检查通过的连续运动点（按加入顺序执行，可混合 TCP / 关节点）"
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
    text="执行前按实机当前关节完成台子/地面预检；仅执行已验证方案。驱动报断连时复核实际到位；未到位或其他异常时中止。",
    fg="#555555"
).pack(anchor=tk.W, padx=15, pady=4)

real_deviation_var = tk.StringVar(value="500.0")
frame_deviation = tk.Frame(root)
frame_deviation.pack(fill=tk.X, padx=10, pady=3)
tk.Label(frame_deviation, text="预检MoveJ兜底最大TCP偏离(mm)：").pack(side=tk.LEFT)
tk.Entry(frame_deviation, textvariable=real_deviation_var, width=10).pack(side=tk.LEFT)
tk.Label(frame_deviation, text="默认500：与TCP仿真/轨迹7~11验证口径一致；实机速度保持20 mm/s").pack(side=tk.LEFT, padx=8)

# v14p：法兰补偿MOVL开关（默认关）。v14l 实机判决驱动 MOVL 无工具补偿（按法兰执行，v14l
# 无补偿直发已拉黑勿回归）；v14p 将错就错：发送瞬间站内工具置单位变换，MoveL(joints) 的
# 笛卡尔目标即法兰位姿，法兰被精确送达→物理尖端走在认证直线上。适用：MoveL 细分段≤150mm
# 且姿态恒定（当前谱系 P5/P9）；规划/预检/几何零改动；失败指纹照旧即停，去勾即回细分路径。
real_movldirect_var = tk.BooleanVar(value=False)
frame_movldirect = tk.Frame(root)
frame_movldirect.pack(fill=tk.X, padx=10, pady=3)
tk.Checkbutton(
    frame_movldirect, variable=real_movldirect_var,
    text="v14u 法兰补偿MOVL+到位纠偏：短直线段(≤150mm)一指令直发，落点法兰级验收(≤8mm/1°)+MoveJ收口（默认关，去勾即回细分）"
).pack(side=tk.LEFT)

# ---- 日志区 ----
frame_log = tk.LabelFrame(root, text="日志")
frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

text_log = scrolledtext.ScrolledText(frame_log, font=("Consolas", 10), height=8)
text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ============================================================
# 启动
# ============================================================
log("机器人: " + robot.Name())
log("程序就绪。" + LOG_VERSION + " ｜ 模式：RUNMODE_RUN_ROBOT + robot.Connect() ｜ 文件日志：" + LOG_PATH)
log("单点：输入坐标 -> 检测可达性 -> 执行 MoveL/MoveJ")
log("目标关节：输入 J1~J6 -> 实机 MoveJ（不经过 TCP/Fanuc 转换和 IK）")
log("连续运动（P2P v14u）：MoveJ 直达优先；前视选解（换向可行性）+前视绑定执行；同位姿停顿不重选；弧碰退回 MoveL；死路分支救援+避障选解；换向碰撞自动换向（反方向坐标修复）/回绕/切分支/MoveL到场；首点种子枚举+整段重试；长运动不分瓣一指令直达（MoveL 仍细分，步长20mm；断连等待与重连并行——v14o 静默重连；可选 v14u 法兰补偿MOVL：短直线≤150mm 一指令直发+法兰级验收+MoveJ纠偏，默认关）。")

def _log_pump():
    try:
        while True:
            text_log.insert(tk.END, _log_queue.get_nowait() + NL)
            text_log.see(tk.END)
    except Exception:
        pass
    root.after(100, _log_pump)


def _on_close():
    if _real_running:
        from tkinter import messagebox as _mb
        if not _mb.askyesno('任务执行中', '实机任务仍在执行，关闭窗口会中断监控。确定关闭？'):
            return
    root.destroy()


root.protocol('WM_DELETE_WINDOW', _on_close)
root.after(100, _log_pump)
_start_heartbeat()
try:
    root.mainloop()
except BaseException:
    import traceback
    _file_log('FATAL mainloop: ' + traceback.format_exc())
    raise
