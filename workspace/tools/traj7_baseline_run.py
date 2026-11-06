#!/usr/bin/env python3
"""无头基准运行：用 AST 从 机械臂TCP仿真.py 原样提取全部模块级函数，
导入 连续轨迹7.json，走与 GUI「执行整段连续运动」完全相同的路径：
_retreat_orientation_records -> _plan_continuous_trajectory -> 逐点仿真运动。
不复制任何逻辑；RUNMODE_SIMULATE，只动 RoboDK 模型。
"""
import ast
import json
import sys
import time

from robodk.robolink import *  # noqa: F401,F403  (与原脚本同款导入)
from robodk.robomath import *  # noqa: F401,F403

SCRIPT = sys.argv[1] if len(sys.argv) > 1 else "机械臂TCP仿真.py"
TRAJ = "连续轨迹7.json"

# ---- 1) AST 提取原脚本全部模块级函数与常量 ----
src = open(SCRIPT, encoding="utf-8").read()
tree = ast.parse(src)
picked = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        picked.append(ast.get_source_segment(src, node))
    elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in ("SIM_SPEED", "ALLOW_SIMULATION", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "_plan_cache"):
            picked.append(ast.get_source_segment(src, node))
print("[runner] 提取 %d 个顶层对象（含常量）" % len(picked), flush=True)

# ---- 2) 计时日志 ----
t_start = time.perf_counter()


def tlog(msg):
    print("[%7.1fs] %s" % (time.perf_counter() - t_start, msg), flush=True)


ns = {"log": tlog, "RDK": None}  # RDK/robot 稍后注入；先占位让 exec 通过
exec("import math\nimport itertools\nimport json\nimport threading\n", ns)
exec("\n\n".join(picked), ns)
tlog("函数体已注入命名空间")

# 星号导入在 exec 环境下不带出 robomath 全部符号，显式补齐（与原脚本 from ... import * 等效）
import robodk.robomath as _rm
for _n in dir(_rm):
    if not _n.startswith("_"):
        ns.setdefault(_n, getattr(_rm, _n))
import robodk.robolink as _rl
for _n in dir(_rl):
    if not _n.startswith("_"):
        ns.setdefault(_n, getattr(_rl, _n))
tlog("robomath/robolink 符号已补齐")

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
ns["RDK"] = RDK
ns["robot"] = robot


class _DevVar:
    """代替 GUI 的 movej_deviation_var（默认 500mm，与界面默认一致）。"""

    def get(self):
        return 500.0


ns["movej_deviation_var"] = _DevVar()
ns["simulation_running"] = False  # 原脚本模块级全局（execute_recorded_trajectory 读它）
ns["trajectory_records"] = []     # 部分函数默认参数引用它

# ---- 3) 给预检函数套计时壳（不改行为，只统计）----
STATS = {}
WRAP_NAMES = ["_enable_obstacle_checks", "_trajectory_start_candidates",
              "_linear_path_endpoint", "_linear_path_endpoint_uncached",
              "_obstacle_joint_target", "_obstacle_joint_target_uncached",
              "_movej_test_cached",
              "_check_movej_tcp_trajectory", "_checked_j6_rewinds",
              "_verify_obstacle_plan", "_plan_continuous_trajectory",
              "_retreat_orientation_records"]
for name in WRAP_NAMES:
    if name not in ns:  # 原版脚本没有 *_uncached/_movej_test_cached/_plan_cache
        continue
    orig = ns[name]

    def make_wrapper(fname, f):
        def wrapper(*a, **kw):
            t0 = time.perf_counter()
            try:
                return f(*a, **kw)
            finally:
                dt = time.perf_counter() - t0
                st = STATS.setdefault(fname, [0, 0.0])
                st[0] += 1
                st[1] += dt
                if dt > 2.0:
                    tlog("  %s 第%d次耗时 %.1fs" % (fname, st[0], dt))
        return wrapper

    ns[name] = make_wrapper(name, orig)

# ---- 4) 导入轨迹（与 import_trajectory 相同的记录结构）----
data = json.load(open(TRAJ, encoding="utf-8"))
records = []
for item in data:
    is_sing = bool(item.get("singular", False)) and item["type"] == "TCP"
    records.append({
        "type": item["type"],
        "values": item["values"][:],
        "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
        "joints": None,
        "singular": is_sing,
        "j6_delta": int(item.get("j6_delta", 180)) if is_sing else 0,
    })
tlog("轨迹已加载：%d 点（特异点 %d 个）" % (len(records), sum(1 for r in records if r["singular"])))
tlog("起始模型关节: %s" % [round(v, 3) for v in robot.Joints().list()[:6]])
tlog("RunMode=%s  开始整段预检+仿真（与 GUI 执行按钮同路径）..." % RDK.RunMode())

# ---- 5) 执行（execute_recorded_trajectory 内部自置 RUNMODE_SIMULATE）----
rc = 0
try:
    ns["execute_recorded_trajectory"](records, tlog)
except Exception as e:  # 兜底：execute 自己也捕获；这里防外层意外
    tlog("!! 外层异常: %s: %s" % (type(e).__name__, e))
    rc = 1

tlog("==== 各阶段耗时统计 ====")
for name in WRAP_NAMES:
    if name in STATS:
        cnt, tot = STATS[name]
        tlog("  %-32s %4d 次  %8.1f s" % (name, cnt, tot))
tlog("总耗时 %.1f s；结束关节: %s" % (time.perf_counter() - t_start,
                                      [round(v, 3) for v in robot.Joints().list()[:6]]))
sys.exit(rc)
