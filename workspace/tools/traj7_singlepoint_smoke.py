#!/usr/bin/env python3
"""单点选项卡路径冒烟测试：复用 runner 的注入环境，走
_obstacle_joint_target -> _check_single_joint_path 这条单点预检链。
使用轨迹 7 的 P1 目标（+500, 0, +300, 180, 0, 0）。
"""
import ast
import time

from robodk.robolink import *  # noqa: F401,F403
from robodk.robomath import *  # noqa: F401,F403

SCRIPT = "机械臂TCP仿真.py"

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


def tlog(msg):
    print("[%6.2fs] %s" % (time.perf_counter() - t_start, msg), flush=True)


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
        q = getattr(_DevVar, "value", 500.0)
        return q


ns["movej_deviation_var"] = _DevVar()
ns["simulation_running"] = False
ns["trajectory_records"] = []

# ---- 单点路径：目标 = 轨迹7 P1 ----
values = [500.0, 0.0, 300.0, 180.0, 0.0, 0.0]
tlog("单点冒烟：目标 %s" % values)
t0 = time.perf_counter()
try:
    end = ns["_obstacle_joint_target"](robot.Joints().list()[:6], values, None, tlog)
    tlog("  _obstacle_joint_target OK：J6=%+.3f°（%.2fs）" % (end[5], time.perf_counter() - t0))
except ValueError as exc:
    tlog("  _obstacle_joint_target 拒绝：%s（%.2fs）" % (str(exc)[:80], time.perf_counter() - t0))
    raise SystemExit(1)

t0 = time.perf_counter()
try:
    ns["_check_single_joint_path"](end)
    tlog("  _check_single_joint_path OK（%.2fs）" % (time.perf_counter() - t0))
except ValueError as exc:
    tlog("  _check_single_joint_path 拒绝：%s" % str(exc)[:80])
    raise SystemExit(1)
tlog("单点路径冒烟通过 ✓")
