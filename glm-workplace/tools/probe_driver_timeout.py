#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 零运动复现实验：验证「93秒预检期间驱动空闲超时断连」假设
# —— 复刻 GUI 预检代码路径（RUNMODE_SIMULATE，不发运动指令），
#    期间每2秒记录一次 ConnectedState / RunMode，捕捉驱动死亡的精确时点。
import io, sys, time, threading
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

SRC = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"
JSON7 = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json"
OUT = r"D:\mydata\glm-workplace\sim_scripts\driver_timeout_probe.txt"

import json

# ---------- 阶段0：连接驱动（对齐 GUI 的 ensure_connected）----------
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, RUNMODE_SIMULATE
from robodk.robomath import pose_angle, invH, norm, Fanuc_2_Pose, Pose_2_Fanuc

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
print("robot:", robot.Name())

def stamp(): return time.strftime("%H:%M:%S")

status0, msg0 = robot.ConnectedState()
print("[%s] 初始 ConnectedState: status=%s msg=%r RunMode=%s" % (stamp(), status0, msg0, RDK.RunMode()))
if status0 != 0:
    print("[%s] 驱动未就绪，先 Connect()（与 GUI ensure_connected 一致）..." % stamp())
    robot.Connect()
    time.sleep(1.5)
    status1, msg1 = robot.ConnectedState()
    print("[%s] Connect() 后: status=%s msg=%r" % (stamp(), status1, msg1))
    if status1 != 0:
        print("!! 驱动无法就绪，实验终止（不发任何运动指令）。")
        sys.exit(1)

log_lines = []

def probe(tag):
    try:
        s, m = robot.ConnectedState()
        line = "[%s] %-14s status=%s msg=%r RunMode=%s" % (stamp(), tag, s, m, RDK.RunMode())
    except Exception as e:
        line = "[%s] %-14s 探测异常: %s" % (stamp(), tag, e)
    print(line)
    log_lines.append(line)

stop_flag = threading.Event()

def monitor():
    n = 0
    while not stop_flag.is_set():
        stop_flag.wait(2.0)
        if stop_flag.is_set():
            break
        n += 1
        probe("监控#%d" % n)

# ---------- 阶段1：预检代码路径（与 GUI 相同，零运动）----------
import ast

KEEP_ASSIGN = {"_plan_cache", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "fanuc_values_to_pose", "pose_to_fanuc_values"}
KEEP_FUNCS = ["_validated_records", "_retreat_orientation_records", "_cache_key_joints", "_cache_key_pose",
              "_movej_test_cached", "_tcp_target_to_flange", "_flange_target_description",
              "_point_to_segment_distance", "_tcp_position_from_joints", "_trajectory_pose",
              "_check_movej_tcp_trajectory", "_collision_details", "_enable_obstacle_checks",
              "_linear_path_endpoint", "_linear_path_endpoint_uncached",
              "_obstacle_posture_key", "_obstacle_joint_target", "_obstacle_joint_target_uncached",
              "_verify_obstacle_plan", "_trajectory_start_candidates", "_checked_j6_rewinds",
              "_plan_continuous_trajectory", "fanuc_to_pose", "pose_to_fanuc"]

src = io.open(SRC, encoding="utf-8").read()
tree = ast.parse(src)
mod = ast.Module(body=[n for n in tree.body
                       if (isinstance(n, ast.FunctionDef) and n.name in KEEP_FUNCS)
                       or (isinstance(n, ast.Assign)
                           and isinstance(n.targets[0], ast.Name)
                           and n.targets[0].id in KEEP_ASSIGN)],
                 type_ignores=[])

ns = {"RDK": RDK, "math": __import__("math"), "itertools": __import__("itertools"),
      "time": time, "log": lambda s: print("[plan]", s),
      "pose_angle": pose_angle, "invH": invH, "norm": norm,
      "RUNMODE_SIMULATE": RUNMODE_SIMULATE,
      "Fanuc_2_Pose": Fanuc_2_Pose, "Pose_2_Fanuc": Pose_2_Fanuc}
# 补充 GUI 里 import * 带来的名字（robomath 全量）
import robodk.robomath as rm
for name in dir(rm):
    if not name.startswith("_"):
        ns.setdefault(name, getattr(rm, name))
from robodk.robolink import COLLISION_ON, COLLISION_OFF, ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, RUNMODE_RUN_ROBOT
ns["COLLISION_ON"] = COLLISION_ON; ns["COLLISION_OFF"] = COLLISION_OFF
ns["ITEM_TYPE_OBJECT"] = ITEM_TYPE_OBJECT; ns["ITEM_TYPE_TOOL"] = ITEM_TYPE_TOOL
ns["RUNMODE_RUN_ROBOT"] = RUNMODE_RUN_ROBOT
ns["robot"] = RDK.Item("", ITEM_TYPE_ROBOT)

exec(compile(mod, SRC, "exec"), ns)

data = json.load(io.open(JSON7, encoding="utf-8"))
records = ns["_validated_records"](data)
expanded = ns["_retreat_orientation_records"](records)
print("轨迹7：%d 点 -> 退让展开 %d 点" % (len(records), len(expanded)))

start = ns["robot"].Joints().list()[:6]
print("起始关节:", ["%.2f" % v for v in start])

RDK.setRunMode(RUNMODE_SIMULATE)
probe("预检开始前")

mt = threading.Thread(target=monitor, daemon=True)
mt.start()
t0 = time.time()
try:
    plan = ns["_plan_continuous_trajectory"](expanded, 500.0, ns["log"])
    print("整段预检通过：%d 步，耗时 %.1fs" % (len(plan), time.time() - t0))
except Exception as exc:
    print("!! 预检失败（%.1fs）：%s: %s" % (time.time() - t0, type(exc).__name__, exc))
finally:
    stop_flag.set()
    mt.join(timeout=3)
    ns["robot"].setJoints(start)
    RDK.setRunMode(RUNMODE_SIMULATE)

probe("预检结束后")
print("关节已还原:", ["%.2f" % v for v in ns["robot"].Joints().list()[:6]])

with io.open(OUT, "a", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
print("监控日志已追加至:", OUT)
