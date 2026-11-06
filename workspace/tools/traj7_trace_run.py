#!/usr/bin/env python3
"""诊断运行：优化版代码 + 逐调用跟踪。
目的：定位与基准日志的分支差异（基准有一条 P3 失败分支，优化版没有）。
输出：_traj7_trace.log（每步判定）+ _traj7_seeds.txt（种子清单）。
"""
import ast
import json
import sys
import time

from robodk.robolink import *  # noqa: F401,F403
from robodk.robomath import *  # noqa: F401,F403

SCRIPT = "机械臂TCP仿真.py"
TRAJ = "连续轨迹7.json"

src = open(SCRIPT, encoding="utf-8").read()
tree = ast.parse(src)
picked = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        picked.append(ast.get_source_segment(src, node))
    elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in ("SIM_SPEED", "ALLOW_SIMULATION", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "_plan_cache"):
            picked.append(ast.get_source_segment(src, node))

t_start = time.perf_counter()
TRACE = open("_traj7_trace.log", "w", encoding="utf-8")


def tlog(msg):
    print("[%7.1fs] %s" % (time.perf_counter() - t_start, msg), flush=True)
    TRACE.write("[%7.1fs] %s\n" % (time.perf_counter() - t_start, msg))
    TRACE.flush()


ns = {"log": tlog, "RDK": None}
exec("import math\nimport itertools\nimport json\nimport threading\n", ns)
exec("\n\n".join(picked), ns)
import robodk.robomath as _rm
for _n in dir(_rm):
    if not _n.startswith("_"):
        ns.setdefault(_n, getattr(_rm, _n))
import robodk.robolink as _rl
for _n in dir(_rl):
    if not _n.startswith("_"):
        ns.setdefault(_n, getattr(_rl, _n))

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
ns["RDK"] = RDK
ns["robot"] = robot


class _DevVar:
    def get(self):
        return 500.0


ns["movej_deviation_var"] = _DevVar()
ns["simulation_running"] = False
ns["trajectory_records"] = []

# ---- 跟踪壳：逐调用记录 ----
_orig_linear = ns["_linear_path_endpoint"]
_orig_lin_unc = ns["_linear_path_endpoint_uncached"]
_orig_obst = ns["_obstacle_joint_target"]
_orig_cands = ns["_trajectory_start_candidates"]
_lin_calls = [0]
_obst_calls = [0]


def linear_traced(start, target):
    _lin_calls[0] += 1
    n = _lin_calls[0]
    hit = ('linear', ns["_cache_key_joints"](start), ns["_cache_key_pose"](target)) in ns["_plan_cache"]
    t0 = time.perf_counter()
    result = _orig_linear(start, target)
    end, detail = result
    tlog("LIN#%02d %s startJ6=%+8.2f -> y=%+7.1f %s (%.2fs)%s"
         % (n, "HIT " if hit else "MISS", start[5], target.Pos()[1],
            "OK " if end is not None else "FAIL", time.perf_counter() - t0,
            "" if end is not None else " | " + detail[:60]))
    return result


def obst_traced(start, values, max_deviation=None, log=None):
    _obst_calls[0] += 1
    n = _obst_calls[0]
    key = ('obstacle', ns["_cache_key_joints"](start), tuple(round(float(v), 6) for v in values[:6]),
           round(float(max_deviation), 6) if max_deviation is not None else None)
    hit = key in ns["_plan_cache"]
    t0 = time.perf_counter()
    try:
        result = _orig_obst(start, values, max_deviation, log)
        tlog("OBST#%02d %s startJ6=%+8.2f -> y=%+7.1f OK endJ6=%+8.2f (%.2fs)"
             % (n, "HIT " if hit else "MISS", start[5], values[1], result[5], time.perf_counter() - t0))
        return result
    except ValueError as exc:
        tlog("OBST#%02d %s startJ6=%+8.2f -> y=%+7.1f RAISE %s (%.2fs)"
             % (n, "HIT " if hit else "MISS", start[5], values[1], str(exc)[:50], time.perf_counter() - t0))
        raise


def cands_traced(records, lower, upper, start):
    result = _orig_cands(records, lower, upper, start)
    if len(records) > 5:  # 外层调用：整段规划的种子清单
        with open("_traj7_seeds.txt", "w", encoding="utf-8") as f:
            f.write("seeds=%d (from %d records)\n" % (len(result) if result else 0, len(records)))
            if result:
                for i, s in enumerate(result):
                    f.write("seed%02d: %s\n" % (i, ["%+.3f" % v for v in s]))
            else:
                f.write("seed00: [] (JOINT start?)\n")
        tlog("外层种子清单已写入 _traj7_seeds.txt：%d 个" % (len(result) if result else 0))
    return result


ns["_linear_path_endpoint"] = linear_traced
ns["_obstacle_joint_target"] = obst_traced
ns["_trajectory_start_candidates"] = cands_traced

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

rc = 0
try:
    ns["execute_recorded_trajectory"](records, tlog)
except Exception as e:
    tlog("!! 外层异常: %s: %s" % (type(e).__name__, e))
    rc = 1

tlog("总耗时 %.1f s；LIN 调用 %d 次；OBST 调用 %d 次；结束关节: %s"
     % (time.perf_counter() - t_start, _lin_calls[0], _obst_calls[0],
        [round(v, 3) for v in robot.Joints().list()[:6]]))
TRACE.close()
sys.exit(rc)
