#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 纯仿真复现：连续轨迹7 在升级版逻辑下整段预检（不连控制器、不发运动指令）
# —— 复刻 _execute_checked_real 的前半段（_validated_records -> 退让展开 -> _prepare_real_plan）
import io, sys, ast, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

SRC = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"
JSON7 = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json"

src = io.open(SRC, encoding="utf-8").read()
data = json.load(io.open(JSON7, encoding="utf-8")) if (json := __import__("json")) else None
print("轨迹7 点数:", len(data))

# AST 提取升级脚本的关键函数，在仿真命名空间执行
KEEP_ASSIGN = {"_plan_cache", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "fanuc_values_to_pose", "pose_to_fanuc_values"}
KEEP_FUNCS = ["_validated_records", "_retreat_orientation_records", "_cache_key_joints", "_cache_key_pose",
              "_movej_test_cached", "_tcp_target_to_flange", "_flange_target_description",
              "_point_to_segment_distance", "_tcp_position_from_joints", "_trajectory_pose",
              "_check_movej_tcp_trajectory", "_collision_details", "_enable_obstacle_checks",
              "_linear_path_endpoint", "_linear_path_endpoint_uncached",
              "_obstacle_posture_key", "_obstacle_joint_target", "_obstacle_joint_target_uncached",
              "_verify_obstacle_plan", "_trajectory_start_candidates", "_checked_j6_rewinds",
              "_plan_continuous_trajectory", "fanuc_to_pose", "pose_to_fanuc"]

tree = ast.parse(src)
mod = ast.Module(body=[n for n in tree.body
                       if (isinstance(n, ast.FunctionDef) and n.name in KEEP_FUNCS)
                       or (isinstance(n, ast.Assign)
                           and isinstance(n.targets[0], ast.Name)
                           and n.targets[0].id in KEEP_ASSIGN)],
                 type_ignores=[])

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, RUNMODE_SIMULATE, RUNMODE_RUN_ROBOT, COLLISION_ON, COLLISION_OFF, ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL
from robodk.robomath import *
from robodk.robomath import pose_angle, invH, norm, Fanuc_2_Pose, Pose_2_Fanuc
ns = {"RDK": Robolink(), "math": __import__("math"), "itertools": __import__("itertools"),
      "time": time, "log": lambda s: print("[plan]", s),
      "pose_angle": pose_angle, "invH": invH, "norm": norm,
      "RUNMODE_SIMULATE": RUNMODE_SIMULATE, "RUNMODE_RUN_ROBOT": RUNMODE_RUN_ROBOT,
      "COLLISION_ON": COLLISION_ON, "COLLISION_OFF": COLLISION_OFF,
      "Fanuc_2_Pose": Fanuc_2_Pose, "Pose_2_Fanuc": Pose_2_Fanuc,
      "ITEM_TYPE_OBJECT": ITEM_TYPE_OBJECT, "ITEM_TYPE_TOOL": ITEM_TYPE_TOOL}
ns["robot"] = ns["RDK"].Item("", ITEM_TYPE_ROBOT)
print("robot:", ns["robot"].Name(), " RunMode:", ns["RDK"].RunMode())
exec(compile(mod, SRC, "exec"), ns)

# 复刻执行入口前半段
records = ns["_validated_records"](data)
print("validated:", len(records), "点")
expanded = ns["_retreat_orientation_records"](records)
print("退让展开后:", len(expanded), "点（原 %d）" % len(records))

start = ns["robot"].Joints().list()[:6]
print("起始关节:", ["%.2f" % v for v in start])
RDK = ns["RDK"]
RDK.setRunMode(RUNMODE_SIMULATE)
t0 = time.time()
try:
    plan = ns["_plan_continuous_trajectory"](expanded, 500.0, ns["log"])
    print("整段预检通过：%d 步，耗时 %.1fs" % (len(plan), time.time() - t0))
    for i, s in enumerate(plan, 1):
        print("  P%-3d %-6s J6=%+8.2f rewinds=%d %s" % (i, s["method"], s["joints"][5],
              len(s["rewinds"]), "特异%+d" % s["j6_delta"] if s["j6_delta"] else ""))
except Exception as exc:
    print("!! 预检失败（%.1fs）：%s: %s" % (time.time() - t0, type(exc).__name__, exc))
finally:
    ns["robot"].setJoints(start)
    RDK.setRunMode(RUNMODE_SIMULATE)
print("关节已还原:", ["%.2f" % v for v in ns["robot"].Joints().list()[:6]])
