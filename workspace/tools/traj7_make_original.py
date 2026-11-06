#!/usr/bin/env python3
"""从当前（已打补丁的）机械臂TCP仿真.py 逆向重建原版文件，用于对照运行。
逐块逆向 2026-09-25 打的 11 个优化 hunk；重建结果做编译自检。
"""
import py_compile

SRC = "机械臂TCP仿真.py"
DST = "_traj7_original_repro.py"

cache_block = '''
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
    return _plan_cache[key]'''

# (current, original) 逐对；顺序无关（各块互不重叠）
REPL = [
    # 1) 常量区缓存块
    ("MOVEJ_FALLBACK_MAX_DEVIATION_MM = 500.0  # MoveL失败后，MoveJ轨迹允许偏离TCP直线段的最大距离\r\n" + cache_block,
     "MOVEJ_FALLBACK_MAX_DEVIATION_MM = 500.0  # MoveL失败后，MoveJ轨迹允许偏离TCP直线段的最大距离"),
    # 2) _linear_path_endpoint 包装
    ('''def _linear_path_endpoint(start, target):
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
    program = RDK.AddProgram('_TCP仿真_路径预检', robot)''',
     '''def _linear_path_endpoint(start, target):
    status = robot.MoveL_Test(start, target, minstep_mm=1)
    if status != 0:
        return None, f'MoveL原生路径检查未通过（{status}）：' + _collision_details()
    # 本机MoveL_Test返回成功后Joints()可能为全零；从插补矩阵读取实际终点。
    program = RDK.AddProgram('_TCP仿真_路径预检', robot)'''),
    # 3) 终点提取碰撞开关
    ("        message, matrix, status = program.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_OFF)\r\n        if status < 0:\r\n            return None, message",
     "        message, matrix, status = program.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_ON)\r\n        if status < 0:\r\n            return None, message"),
    # 4) _obstacle_joint_target 包装
    ('''def _obstacle_joint_target(start, values, max_deviation=None, log=None):
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
    lower, upper, _ = robot.JointLimits()''',
     '''def _obstacle_joint_target(start, values, max_deviation=None, log=None):
    lower, upper, _ = robot.JointLimits()'''),
    # 5) 兜底精查
    ("            if _movej_test_cached(start, end, .25) == 0:",
     "            if robot.MoveJ_Test(start, end, minstep_deg=.25) == 0:"),
    # 6) _checked_j6_rewinds
    ('''def _checked_j6_rewinds(q, lower, upper, max_deviation):
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
    return [r[:] for r in results]''',
     '''def _checked_j6_rewinds(q, lower, upper, max_deviation):
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
            yield end'''),
    # 7) 单点MoveJ
    ("        if _movej_test_cached(saved, end, 1) != 0:\r\n            raise ValueError('单点MoveJ路径被拒绝：' + _collision_details())",
     "        if robot.MoveJ_Test(saved, end, minstep_deg=1) != 0:\r\n            raise ValueError('单点MoveJ路径被拒绝：' + _collision_details())"),
    # 8) 起始姿态
    ("    if _movej_test_cached(saved, saved, 1) != 0:\r\n        raise ValueError('起始姿态已碰撞，不能自动规划脱离：' + _collision_details())",
     "    if robot.MoveJ_Test(saved, saved, minstep_deg=1) != 0:\r\n        raise ValueError('起始姿态已碰撞，不能自动规划脱离：' + _collision_details())"),
    # 9) 规划循环内 MoveJ 检查
    ("                        if method == 'MoveJ' and _movej_test_cached(q, end, 1) != 0:\r\n                            raise ValueError(f'P{i}：MoveJ路径检查失败：' + _collision_details())",
     "                        if method == 'MoveJ' and robot.MoveJ_Test(q, end, minstep_deg=1) != 0:\r\n                            raise ValueError(f'P{i}：MoveJ路径检查失败：' + _collision_details())"),
    # 10) 缓存清空
    ('''def _enable_obstacle_checks():
    if RDK.RunMode() != RUNMODE_SIMULATE:
        raise RuntimeError('障碍物预检仅允许在仿真模式执行。')
    # 每次进入预检都清空预检缓存：缓存生命周期 = 单次预检规划，
    # 障碍物/工作站状态的变化在下一次预检即时生效。
    _plan_cache.clear()''',
     '''def _enable_obstacle_checks():
    if RDK.RunMode() != RUNMODE_SIMULATE:
        raise RuntimeError('障碍物预检仅允许在仿真模式执行。')'''),
    # 11) 启动日志
    ('log("连续运动升级版：TCP自动换算法兰位姿；MoveJ先粗筛再精查，合格即采用；特异点仅J6自动±180°，保留碰撞和偏离检查；预检带结果缓存与MoveL粗筛（安全判定粒度不变）。")',
     'log("连续运动升级版：TCP自动换算法兰位姿；MoveJ先粗筛再精查，合格即采用；特异点仅J6自动±180°，保留碰撞和偏离检查。")'),
]

src = open(SRC, "rb").read().decode("utf-8")
# 脚本内字面量是 LF，磁盘文件是 CRLF：统一到 CRLF 再匹配
REPL = [(c.replace("\r\n", "\n").replace("\n", "\r\n"),
         o.replace("\r\n", "\n").replace("\n", "\r\n")) for c, o in REPL]
for i, (cur, orig) in enumerate(REPL, 1):
    if src.count(cur) != 1:
        raise SystemExit("块 %d 匹配 %d 次（应为 1），中止" % (i, src.count(cur)))
    src = src.replace(cur, orig)
open(DST, "w", encoding="utf-8", newline="").write(src)
py_compile.compile(DST, doraise=True)
print("原版已重建并编译通过：%s（%d 字符）" % (DST, len(src)))
