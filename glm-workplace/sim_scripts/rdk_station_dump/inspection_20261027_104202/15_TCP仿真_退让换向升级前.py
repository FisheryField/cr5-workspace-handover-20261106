# -*- coding: utf-8 -*-
"""
RoboDK 仿真：单点 + 连续运动（支持 TCP / 关节混合，含导入导出）
- 单点：指定 TCP -> IK 检查 -> MoveJ/MoveL
- 连续：逐点添加 TCP/关节 -> 检查可达性 -> 批量执行
姿态格式：Fanuc/Motoman
"""

from robodk.robolink import *
from robodk.robomath import *

import tkinter as tk
from tkinter import ttk, filedialog
import threading
import math
import json
import itertools

SIM_SPEED = 50.0
ALLOW_SIMULATION = True
MOVEJ_FALLBACK_MAX_DEVIATION_MM = 500.0  # MoveL失败后，MoveJ轨迹允许偏离TCP直线段的最大距离

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)

if not robot.Valid():
    RDK.ShowMessage("未找到机械臂！", False)
    raise Exception("未找到机械臂")

# ============================================================
# Fanuc/Motoman 转换
# ============================================================
def fanuc_values_to_pose(x, y, z, rx, ry, rz):
    return Fanuc_2_Pose([x, y, z, rx, ry, rz])

def pose_to_fanuc_values(pose):
    return Pose_2_Fanuc(pose)

# ============================================================
# 全局变量（单点）
# ============================================================
target_pose = None
target_joints = None
simulation_running = False

# ============================================================
# 全局变量（连续运动）
# ============================================================
trajectory_records = []          # 存储 {'type':'TCP'/'JOINT', 'values':[...], 'target':pose, 'joints':[...]}
record_text = None
traj_entries = None
traj_type = None
traj_singular = None          # 当前输入 TCP 是否标记为末端特异点
traj_j6_direction = None      # 特异点 J6 转动方向：+180 / -180

# ============================================================
# GUI 构建
# ============================================================
root = tk.Tk()
root.title("RoboDK - 机械臂仿真控制（轨迹预检升级版）")
root.geometry("1200x750")
root.resizable(True, True)

# ---- Notebook ----
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# ============================================================
# 选项卡 1：单点运动（保留原有功能）
# ============================================================
tab_single = ttk.Frame(notebook)
notebook.add(tab_single, text="单点运动")

input_frame = tk.LabelFrame(tab_single, text="目标 TCP（Fanuc/Motoman 格式）")
input_frame.pack(fill=tk.X, padx=10, pady=10)

names = ["X (mm)", "Y (mm)", "Z (mm)", "Rx (deg)", "Ry (deg)", "Rz (deg)"]
defaults = ["0.000", "-241.500", "1047.000", "-90.000", "0.000", "180.000"]
entries_single = []

for i in range(6):
    tk.Label(input_frame, text=names[i]).grid(row=0, column=i*2, padx=5, pady=10)
    e = tk.Entry(input_frame, width=12)
    e.insert(0, defaults[i])
    e.grid(row=0, column=i*2+1, padx=5, pady=10)
    entries_single.append(e)

status_var = tk.StringVar(value="请输入目标点，然后点击“检查目标点”")
tk.Label(tab_single, textvariable=status_var, font=("Microsoft YaHei", 12, "bold")).pack(pady=8)

# 按钮框架
btn_frame_single = tk.Frame(tab_single)
btn_frame_single.pack(fill=tk.X, padx=10, pady=5)

check_button = tk.Button(btn_frame_single, text="检查目标点", command=lambda: check_target(entries_single, status_var, simulate_button, log), width=18, font=("Microsoft YaHei", 10, "bold"))
check_button.pack(side=tk.LEFT, padx=5)

simulate_button = tk.Button(btn_frame_single, text="开始 MoveJ 仿真", command=lambda: start_simulation(entries_single, status_var, simulate_button, check_button, log), width=20, font=("Microsoft YaHei", 10, "bold"), state=tk.DISABLED)
simulate_button.pack(side=tk.LEFT, padx=5)

tk.Button(btn_frame_single, text="停止仿真", command=lambda: stop_simulation(status_var, simulate_button, check_button, log), width=14).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame_single, text="读取当前 TCP", command=lambda: read_current_tcp(log), width=16).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame_single, text="当前 TCP → 输入框", command=lambda: current_tcp_to_input(entries_single, log), width=18).pack(side=tk.LEFT, padx=5)

# ---- 日志（放在最下面）----
log_frame = tk.LabelFrame(tab_single, text="日志")
log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

text_output = tk.Text(log_frame, font=("Consolas", 10), wrap=tk.NONE)
text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_y = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=text_output.yview)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
text_output.configure(yscrollcommand=scroll_y.set)

# ============================================================
# 选项卡 2：连续运动（含导入导出）
# ============================================================
tab_traj = ttk.Frame(notebook)
notebook.add(tab_traj, text="连续运动")

# ---- 输入区域 ----
frame_traj_input = tk.LabelFrame(tab_traj, text="连续运动点输入：每次输入 1 个 TCP 点或 1 组关节角度，点击“检查并加入”")
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

tk.Radiobutton(type_frame, text="TCP（X,Y,Z,Rx,Ry,Rz）", variable=traj_type, value="TCP", command=_update_traj_labels_and_defaults).pack(side=tk.LEFT, padx=8)
tk.Radiobutton(type_frame, text="关节（J1~J6）", variable=traj_type, value="JOINT", command=_update_traj_labels_and_defaults).pack(side=tk.LEFT, padx=8)

# ---- 末端特异点设置 ----
singular_frame = tk.Frame(tab_traj)
singular_frame.pack(fill=tk.X, padx=10, pady=2)
traj_singular = tk.BooleanVar(value=False)
traj_j6_direction = tk.IntVar(value=180)
tk.Checkbutton(
    singular_frame,
    text="标记当前 TCP 为末端特异点（跳过 IK，J6 直接转 180°）",
    variable=traj_singular
).pack(side=tk.LEFT, padx=3)
tk.Label(singular_frame, text="J6优先方向（不可行时自动反向）：").pack(side=tk.LEFT, padx=(15, 2))
tk.Radiobutton(singular_frame, text="+180°", variable=traj_j6_direction, value=180).pack(side=tk.LEFT)
tk.Radiobutton(singular_frame, text="-180°", variable=traj_j6_direction, value=-180).pack(side=tk.LEFT)

movej_check_frame = tk.Frame(tab_traj)
movej_check_frame.pack(fill=tk.X, padx=10, pady=2)
tk.Label(movej_check_frame, text="MoveJ兜底轨迹最大允许偏离TCP直线：").pack(side=tk.LEFT, padx=3)
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
tk.Button(btn_traj_input, text="读取当前TCP并写入", command=lambda: read_current_tcp_to_traj(traj_type, traj_entries, log), width=20).pack(side=tk.LEFT, padx=3)
tk.Button(btn_traj_input, text="读取当前关节并写入", command=lambda: read_current_joints_to_traj(traj_type, traj_entries, log), width=20).pack(side=tk.LEFT, padx=3)
tk.Button(btn_traj_input, text="清空当前输入", command=lambda: clear_trajectory_input(traj_type, traj_entries, log), width=16).pack(side=tk.LEFT, padx=3)

tk.Label(tab_traj, text="普通 TCP 用 IK 判断可达并检查连续段；关节点只做角度规范化。标记为末端特异点的 TCP 跳过 IK，仅在执行时让 J6 转 ±180°，其后的普通 TCP 重新正常 IK。", fg="#555555").pack(anchor=tk.W, padx=15, pady=3)

# ---- 已添加点列表 ----
frame_record = tk.LabelFrame(tab_traj, text="已检查通过的连续运动点（按加入顺序执行，可混合 TCP / 关节点）")
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

# ============================================================
# 核心函数（单点）
# ============================================================
def log(text):
    print(text)
    try:
        text_output.insert(tk.END, str(text) + "\n")
        text_output.see(tk.END)
        traj_log_output.insert(tk.END, str(text) + "\n")
        traj_log_output.see(tk.END)
        if str(text).strip():
            traj_status_var.set(str(text))
        root.update_idletasks()
    except:
        pass

def set_status(text):
    status_var.set(text)

def get_input_values(entries):
    try:
        return [float(e.get()) for e in entries]
    except ValueError:
        log("✕ 输入错误：所有值必须为数字。")
        set_status("输入错误")
        return None

def check_target(entries, status_var, simulate_button, log):
    global target_pose, target_joints
    simulate_button.config(state=tk.DISABLED)
    target_pose = None
    target_joints = None

    values = get_input_values(entries)
    if values is None:
        return

    x, y, z, rx, ry, rz = values
    log("")
    log("============================================================")
    log("开始检查目标点")
    log("============================================================")
    log(f"目标 TCP：X={x:.3f} Y={y:.3f} Z={z:.3f} Rx={rx:.3f} Ry={ry:.3f} Rz={rz:.3f}")

    try:
        pose = fanuc_values_to_pose(x, y, z, rx, ry, rz)
        log(_flange_target_description(pose))
        joints = robot.SolveIK(_tcp_target_to_flange(pose))
    except Exception as e:
        log(f"✕ IK 检查发生错误：{e}")
        set_status("IK 检查失败")
        return

    if joints is None:
        log("✕ SolveIK 返回 None")
        set_status("目标点不可达 ✕")
        return

    q = joints.list()
    if q is None or len(q) < 6:
        log(f"✕ IK 无效：SolveIK 未返回 6 个关节值，实际={q}")
        set_status("目标点 IK 不可用 ✕")
        return

    # IK -> FK 闭环校验
    try:
        fk_pose = _trajectory_pose(joints)
        fk = pose_to_fanuc_values(fk_pose)
        pos_err = ((fk[0]-x)**2 + (fk[1]-y)**2 + (fk[2]-z)**2) ** 0.5
        ang_err = math.degrees(pose_angle(invH(pose) * fk_pose))
        log("")
        log(f"[DEBUG] IK -> FK 验证：FK={fk}, 位置误差={pos_err:.6f} mm, 相对姿态误差={ang_err:.6f} deg")
        if pos_err > 0.5 or ang_err > 0.5:
            log("✕ IK/FK 闭环误差过大，拒绝执行。")
            set_status("IK/FK 验证失败 ✕")
            return
        log("✓ IK/FK 闭环验证通过")
    except Exception as e:
        log(f"✕ IK/FK 验证失败：{e}")
        set_status("IK/FK 验证失败 ✕")
        return

    target_pose = pose
    target_joints = joints

    log("")
    log("✓ 目标点 IK 可达")
    log("满足条件的一组关节角：")
    for i in range(6):
        log(f"J{i+1} = {q[i]:.3f} deg")

    actual = pose_to_fanuc_values(target_pose)
    log("")
    log("RoboDK 对应的 Fanuc/Motoman 姿态：")
    log(f"X={actual[0]:.3f} Y={actual[1]:.3f} Z={actual[2]:.3f} Rx={actual[3]:.3f} Ry={actual[4]:.3f} Rz={actual[5]:.3f}")
    log("")
    log("现在可以点击“开始 MoveJ 仿真”。")
    set_status("目标点可达 ✓，MoveJ 仿真已启用")
    simulate_button.config(state=tk.NORMAL)

def start_simulation(entries, status_var, simulate_button, check_button, log):
    global simulation_running
    if target_pose is None:
        log("✕ 尚未通过目标点检查。")
        return
    if not ALLOW_SIMULATION:
        log("当前禁止仿真运动。")
        return
    if RDK.RunMode() != RUNMODE_SIMULATE:
        log('当前不是仿真模式，单点仿真未启动。')
        return
    if robot.Busy():
        log('机器人正在运动，单点仿真未启动。')
        return
    if simulation_running:
        log("仿真正在运行，请稍候。")
        return

    simulation_running = True
    simulate_button.config(state=tk.DISABLED)
    check_button.config(state=tk.DISABLED)

    def worker():
        global simulation_running
        try:
            log("")
            log("============================================================")
            log("开始 RoboDK 仿真")
            log("============================================================")
            robot.setSpeed(SIM_SPEED)
            log(f"速度：{SIM_SPEED:.1f} mm/s")
            if target_joints is not None:
                _enable_obstacle_checks()
                RDK.Command('Trace', 'Off')
                q = _obstacle_joint_target(robot.Joints().list()[:6], pose_to_fanuc_values(target_pose))
                log("正在运动到目标点（MoveJ，使用 IK 关节）...")
                log(f"J = {[round(float(v), 6) for v in q[:6]]}")
                _check_single_joint_path(q[:6])
                RDK.Command('Trace', 'Reset')
                RDK.Command('Trace', 'On')
                if RDK.RunMode() != RUNMODE_SIMULATE:
                    raise RuntimeError('运行模式改变，单点仿真停止。')
                robot.MoveJ(q[:6])
            else:
                log("✕ 没有有效 IK 关节，拒绝执行 MoveJ。")
                set_status("没有有效 IK，未执行")
                return
            log("")
            log("✓ 仿真完成")
            set_status("仿真完成 ✓")
        except Exception as e:
            log("")
            log(f"✕ 仿真失败：{type(e).__name__}: {e}")
            set_status("仿真失败")
        finally:
            simulation_running = False
            root.after(0, lambda: check_button.config(state=tk.NORMAL))
            root.after(0, lambda: simulate_button.config(state=tk.NORMAL))

    threading.Thread(target=worker, daemon=True).start()

def stop_simulation(status_var, simulate_button, check_button, log):
    global simulation_running
    try:
        robot.Stop()
        log("已发送停止命令。")
        set_status("仿真已停止")
    except Exception as e:
        log(f"停止失败：{e}")
    simulation_running = False
    simulate_button.config(state=tk.NORMAL)
    check_button.config(state=tk.NORMAL)

def read_current_tcp(log):
    try:
        pose = _trajectory_pose(robot.Joints())
        values = pose_to_fanuc_values(pose)
        log("")
        log("============================================================")
        log("当前 RoboDK TCP（Fanuc/Motoman 格式）")
        log("============================================================")
        log(f"X={values[0]:.3f} Y={values[1]:.3f} Z={values[2]:.3f} Rx={values[3]:.3f} Ry={values[4]:.3f} Rz={values[5]:.3f}")
    except Exception as e:
        log(f"读取当前 TCP 失败：{e}")

def current_tcp_to_input(entries, log):
    try:
        pose = _trajectory_pose(robot.Joints())
        values = pose_to_fanuc_values(pose)
        for e, val in zip(entries, values):
            e.delete(0, tk.END)
            e.insert(0, f"{val:.3f}")
        log("✓ 已将当前 RoboDK TCP 填入目标输入框。")
    except Exception as e:
        log(f"读取当前 TCP 失败：{e}")

# ============================================================
# 连续运动核心函数（移植自真实运动脚本，适配仿真）
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
                line = f"P{i:<3} [TCP-特异点 J6优先{sd:+d}°/可反向] X={vals[0]:9.3f} Y={vals[1]:9.3f} Z={vals[2]:9.3f} Rx={vals[3]:8.3f} Ry={vals[4]:8.3f} Rz={vals[5]:8.3f}\n"
            else:
                line = f"P{i:<3} [TCP]   X={vals[0]:9.3f} Y={vals[1]:9.3f} Z={vals[2]:9.3f} Rx={vals[3]:8.3f} Ry={vals[4]:8.3f} Rz={vals[5]:8.3f}\n"
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
            log("TCP IK：不可达")
            return False, None, None
        q = joints.list()
        if len(q) < 6:
            log(f"TCP IK：返回关节数量异常：{q}")
            return False, None, None
        log("TCP IK：可达")
        log(f"  IK关节：J1={q[0]:.2f} J2={q[1]:.2f} J3={q[2]:.2f} J4={q[3]:.2f} J5={q[4]:.2f} J6={q[5]:.2f}")
        return True, target, q[:6]
    except Exception as e:
        log(f"TCP IK 检查失败：{type(e).__name__}: {e}")
        return False, None, None

def _check_tcp_segment_continuous(prev_vals, curr_vals, segment_index, samples=20):
    """检查相邻 TCP 点间插补路径的 IK 连续可达性"""
    if prev_vals is None:
        return True
    log(f"开始检查 P{segment_index-1} -> P{segment_index} 的 TCP 连续 IK（{samples+1} 个采样点）")
    for k in range(samples + 1):
        t = k / samples
        vals = [prev_vals[i] + (curr_vals[i] - prev_vals[i]) * t for i in range(6)]
        try:
            pose = fanuc_values_to_pose(*vals)
            joints = robot.SolveIK(_tcp_target_to_flange(pose))
            if joints is None:
                log(f"  P{segment_index-1} -> P{segment_index}：第 {k+1}/{samples+1} 个采样点 IK 不可达，t={t:.3f}")
                log(f"  TCP：X={vals[0]:.3f} Y={vals[1]:.3f} Z={vals[2]:.3f} Rx={vals[3]:.3f} Ry={vals[4]:.3f} Rz={vals[5]:.3f}")
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
            log("末端特异点前一项必须是普通 TCP 点；否则无法保证只是末端原地旋转 180°。")
            return
        prev_vals = trajectory_records[-1]["values"]
        pos_err = math.sqrt(sum((vals[k] - prev_vals[k]) ** 2 for k in range(3)))
        if pos_err > 1e-3:
            log("末端特异点未加入：它的 XYZ 必须与前一个普通 TCP 点相同。")
            log(f"  与前一点位置差：{pos_err:.6f} mm")
            log("  特异点的设计前提是：只改变末端绕自身轴的姿态，不改变 TCP 位置。")
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
        log(f"P{len(trajectory_records)} [TCP-特异点]：已加入，跳过 IK。")
        log(f"  执行时保持 J1~J5 不变，J6优先转 {j6_delta:+d}°；整段不可行时尝试反向。")
        log("  请确保该点与前一点相比确实只是末端绕自身轴旋转 180°。")
        refresh_record_list(record_text, trajectory_records)
        if singular_var is not None:
            singular_var.set(False)
        return

    if kind == "TCP":
        ok, target, joints = _check_tcp_reachable(vals)
        if not ok:
            log("该 TCP 点未加入轨迹。")
            return

        # 普通 TCP 与前一个普通 TCP 之间做连续 IK 检查。
        # 如果前一个点是末端特异点，则特异点本身跳过 IK；当前点从这里开始重新做普通 SolveIK，
        # 因此不把“特异点姿态 -> 当前姿态”当成普通 TCP 笛卡尔插补段。
        if trajectory_records and trajectory_records[-1]["type"] == "TCP" and not trajectory_records[-1].get("singular", False):
            prev_vals = trajectory_records[-1]["values"]
            segment_no = len(trajectory_records) + 1
            if not _check_tcp_segment_continuous(prev_vals, vals, segment_no, samples=20):
                log(f"P{segment_no} [TCP]：上一 TCP 点到当前 TCP 点的连续 IK 检查失败，该点未加入轨迹。")
                return

        trajectory_records.append({
            "type": "TCP",
            "values": vals[:],
            "target": target,
            "joints": joints,
        })
        log(f"P{len(trajectory_records)} [TCP]：检查通过，已加入连续运动。")
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
        pose = _trajectory_pose(robot.Joints())
        vals = pose_to_fanuc_values(pose)
        log("========== 读取当前 TCP -> 连续运动输入框 ==========")
        log(f"X={vals[0]:+.3f} Y={vals[1]:+.3f} Z={vals[2]:+.3f} Rx={vals[3]:+.3f} Ry={vals[4]:+.3f} Rz={vals[5]:+.3f}")
        if traj_type.get() != "TCP":
            traj_type.set("TCP")
            _update_traj_labels_and_defaults()
        return _write_values_to_traj_entries(vals, "TCP")
    except Exception as e:
        log(f"读取当前 TCP 失败：{type(e).__name__}: {e}")
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
    RDK.setCollisionActive(COLLISION_ON)


def _check_single_joint_path(end):
    _enable_obstacle_checks()
    saved = robot.Joints().list()[:6]
    try:
        RDK.Command('Trace', 'Off')
        RDK.Render(False)
        if robot.MoveJ_Test(saved, end, minstep_deg=1) != 0:
            raise ValueError('单点MoveJ路径被拒绝：' + _collision_details())
    finally:
        robot.setJoints(saved)
        RDK.Render(True)


def _trajectory_pose(q):
    return invH(robot.PoseFrame()) * robot.SolveFK(q) * robot.PoseTool()


def _linear_path_endpoint(start, target):
    status = robot.MoveL_Test(start, target, minstep_mm=1)
    if status != 0:
        return None, f'MoveL原生路径检查未通过（{status}）：' + _collision_details()
    # 本机MoveL_Test返回成功后Joints()可能为全零；从插补矩阵读取实际终点。
    program = RDK.AddProgram('_TCP仿真_路径预检', robot)
    try:
        program.setVisible(False)
        robot.setJoints(start)
        program.setPoseFrame(robot.PoseFrame())
        program.setPoseTool(robot.PoseTool())
        program.MoveJ(start)
        program.MoveL(target)
        message, matrix, status = program.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        if status < 0:
            return None, message
        end = matrix.tr().rows[-1][:6]
        error_pose = invH(target) * _trajectory_pose(end)
        if norm(error_pose.Pos()) > .01 or pose_angle(error_pose) > math.radians(.01):
            raise RuntimeError('路径预检返回的终点不匹配目标TCP。')
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
    lower, upper, _ = robot.JointLimits()
    candidates = _trajectory_start_candidates([dict(type='TCP', values=values)], lower.list(), upper.list(), start)
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
            if robot.MoveJ_Test(start, end, minstep_deg=.25) == 0:
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
            getattr(program, step['method'])(step['joints'])
        message, matrix, status = program.InstructionListJoints(
            mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        if status < 0:
            raise ValueError('整段碰撞复核未通过：' + message)
    finally:
        program.Delete()
        robot.setJoints(saved)


def _trajectory_start_candidates(records, lower, upper, reference=None):
    reference = robot.Joints().list()[:6] if reference is None else reference
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
    """返回可实际执行的整圈回绕；TCP空间偏离和碰撞都必须通过检查。"""
    tcp = pose_to_fanuc_values(_trajectory_pose(q))
    for delta in (-360.0, 360.0):
        end = q[:]
        end[5] += delta
        if not lower[5] <= end[5] <= upper[5]:
            continue
        if not _check_movej_tcp_trajectory(q, end, tcp, tcp, lambda msg: None,
                                          samples=360, max_deviation_mm=max_deviation):
            continue
        if robot.MoveJ_Test(q, end, minstep_deg=1) == 0:
            yield end


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
                raise ValueError(f'P{i+1}：特异点必须紧跟普通TCP点。')
            if rec.get('j6_delta', 180) not in (-180, 180):
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
    if robot.MoveJ_Test(saved, saved, minstep_deg=1) != 0:
        raise ValueError('起始姿态已碰撞，不能自动规划脱离：' + _collision_details())
    candidates = _trajectory_start_candidates(records, lower, upper, saved)
    direction_choices = [(rec.get('j6_delta', 180), -rec.get('j6_delta', 180))
                         for rec in records if rec.get('singular', False)]
    last_error = '首个TCP没有限位内的逆解。'
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
                                raise ValueError(f'P{i}：仅旋转J6无法到达所标注TCP，请检查特异点标记/工具。')
                        elif first_tcp:
                            end = seed[:]
                            first_tcp = False
                        else:
                            end, detail = _linear_path_endpoint(q, target)
                            if end is None and allow_rewind:
                                for rewound in _checked_j6_rewinds(q, lower, upper, max_deviation):
                                    end, detail = _linear_path_endpoint(rewound, target)
                                    if end is not None:
                                        rewinds.append(rewound[:])
                                        q = rewound
                                        break
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
                        if method == 'MoveJ' and robot.MoveJ_Test(q, end, minstep_deg=1) != 0:
                            raise ValueError(f'P{i}：MoveJ路径检查失败：' + _collision_details())
                        plan.append(dict(method=method, joints=end[:], special=special, fallback=fallback, rewinds=rewinds, j6_delta=selected_delta))
                        q = end[:]
                    _verify_obstacle_plan(saved, plan)
                    log(f'整段路径预检通过：{len(plan)}点；首个TCP J6={seed[5]:+.3f}°。' if seed else f'整段路径预检通过：{len(plan)}个关节点。')
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


def execute_recorded_trajectory(trajectory_records, log):
    global simulation_running
    if simulation_running:
        log('已有仿真正在运行，请等待结束。')
        return
    if not ALLOW_SIMULATION or not trajectory_records:
        log('当前禁止仿真或没有轨迹点。')
        return
    simulation_running = True
    completed_count = 0
    trace_owned = False
    i = 0
    try:
        RDK.setRunMode(RUNMODE_SIMULATE)
        if robot.Busy():
            raise RuntimeError('机器人正在执行其他动作，本次未启动。')
        trace_owned = True
        RDK.Command('Trace', 'Off')
        RDK.Command('Trace', 'Reset')
        records = [dict(rec, values=rec['values'][:]) for rec in trajectory_records]
        log(f'========== 整段路径预检：{len(records)}点（仿真模式） ==========')
        plan = _plan_continuous_trajectory(records, float(movej_deviation_var.get()), log)
        RDK.Command('Trace', 'Reset')
        RDK.Command('Trace', 'On')
        log('========== 正式仿真运动：现在仅显示本次实际运动轨迹 ==========')
        robot.setSpeed(SIM_SPEED)
        for i, step in enumerate(plan, 1):
            if RDK.RunMode() != RUNMODE_SIMULATE:
                raise RuntimeError('运行模式改变，停止仿真。')
            for rewound in step['rewinds']:
                before = robot.Joints().list()[:6]
                log(f'P{i}前：实际MoveJ回绕J6 {rewound[5]-before[5]:+.0f}°（{before[5]:+.3f}° → {rewound[5]:+.3f}°），已通过偏离及碰撞检查。')
                robot.MoveJ(rewound)
                if max(abs(a-b) for a, b in zip(robot.Joints().list()[:6], rewound)) > .1:
                    raise RuntimeError('回绕终点与预检关节不一致。')
            log(f'P{i} 开始 {step["method"]}，J6目标={step["joints"][5]:+.3f}°')
            # 执行预检得到的关节分支；运行时异常立即停止，不把停止/通信异常当作兜底请求。
            getattr(robot, step['method'])(step['joints'])
            actual = robot.Joints().list()[:6]
            if max(abs(a-b) for a, b in zip(actual, step['joints'])) > .1:
                raise RuntimeError('实际关节与预检终点不一致。')
            completed_count += 1
            suffix = f'（仅J6 {step["j6_delta"]:+d}°，J1～J5保持不变）' if step['special'] else ('（偏离检查后兜底）' if step['fallback'] else '')
            log(f'P{i} -> {step["method"]} 执行完成{suffix}')
        log(f'========== 连续运动仿真完成：{completed_count}/{len(plan)} 点 ==========')
    except Exception as exc:
        log(f'✕ 连续运动停止：已完成{completed_count}点，阶段={"路径预检" if i == 0 else "P"+str(i)}；{type(exc).__name__}: {exc}')
    finally:
        if trace_owned:
            RDK.Command('Trace', 'Off')
            RDK.Render(True)
        simulation_running = False


# ============================================================
# 启动信息
# ============================================================
log("程序准备完成。")
log(f"机器人：{robot.Name()}")
log("姿态格式：Fanuc/Motoman (XYZ mm, Rx/Ry/Rz deg)")
log("单点运动：输入 TCP -> 检查 IK -> 执行 MoveJ")
log("连续运动升级版：TCP自动换算法兰位姿；MoveJ先粗筛再精查，合格即采用；特异点仅J6自动±180°，保留碰撞和偏离检查。")
log("新增：导入/导出轨迹（JSON 格式）")

root.mainloop()
