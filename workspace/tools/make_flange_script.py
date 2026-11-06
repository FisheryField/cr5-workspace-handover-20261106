#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 机械臂法兰真实运动.py from 机械臂TCP真实运动.py.

Semantics of the new script: every coordinate the operator types or reads is the
robot FLANGE pose (no end tool).  RoboDK's SolveIK/MoveL/MoveJ interpret poses as
TCP, so the flange->TCP conversion (法兰 × 工具) is applied once, at the parse
boundary; the reading side goes the other way and never involves the tool.

Every replacement asserts its hit count so a silent mismatch fails loudly.
"""
import io
import os
import re
import sys

SRC = r"D:\mydata\workspace\机械臂TCP真实运动.py"
DST = r"D:\mydata\workspace\机械臂法兰真实运动.py"

DOC_OLD = '''"""
RoboDK 实机运动控制（基于 robodk_movej_diag.py 的成功模式）
- 单点：TCP 输入 -> IK 检测 -> MoveL/MoveJ 执行
- 连续轨迹：坐标列表 -> 逐点 IK 检测 -> MoveJ+MoveL 序列
模式：RUNMODE_RUN_ROBOT + robot.Connect()
"""'''

DOC_NEW = '''"""
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
"""'''

HELPER_OLD = '''def fanuc_to_pose(x, y, z, rx, ry, rz):
    return Fanuc_2_Pose([x, y, z, rx, ry, rz])

def pose_to_fanuc(pose):
    return Pose_2_Fanuc(pose)'''

HELPER_NEW = '''def _tool_mat():
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
    return invH(robot.PoseFrame()) * robot.SolveFK(robot.Joints())'''

REPLACEMENTS = [
    (DOC_OLD, DOC_NEW, 1, "文件头说明"),
    (HELPER_OLD, HELPER_NEW, 1, "法兰<->TCP 换算helper"),
    # 读取当前位姿：改成法兰
    ("pose = robot.Pose()", "pose = current_flange_pose()", 3, "robot.Pose() -> 法兰"),
    ('log("当前 TCP：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(v[:6]))',
     'log("当前法兰（不含工具）：X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(v[:6]))',
     1, "日志：当前 TCP -> 当前法兰"),
    ('log("当前 TCP 已填入")', 'log("当前法兰（不含工具）已填入")', 1, "日志：已填入"),
    ('log("========== 读取当前 TCP -> 选项卡3 ==========")',
     'log("========== 读取当前法兰 -> 选项卡3 ==========")', 1, "日志：读取当前"),
    ('log("读取当前 TCP 失败：%s: %s" % (type(e).__name__, e))',
     'log("读取当前法兰失败：%s: %s" % (type(e).__name__, e))', 1, "日志：读取失败"),
    # GUI 标签
    ('text="目标 TCP（Fanuc 格式）"', 'text="目标法兰（Fanuc 格式，不含工具）"', 1, "标签：目标"),
    ('text="读取当前 TCP"', 'text="读取当前法兰"', 1, "按钮：读取当前"),
    ('text="当前 TCP -> 输入框"', 'text="当前法兰 -> 输入框"', 1, "按钮：填入输入框"),
    ('text="连续运动点输入：每次输入 1 个 TCP 点或 1 组关节角度，点击“检查并加入”"',
     'text="连续运动点输入：每次输入 1 个法兰位姿或 1 组关节角度，点击“检查并加入”"', 1, "标签：连续输入"),
    ('text="TCP（X,Y,Z,Rx,Ry,Rz）"', 'text="法兰（X,Y,Z,Rx,Ry,Rz，不含工具）"', 3, "单选：类型"),
    ('text="读取当前TCP并写入"', 'text="读取当前法兰并写入"', 1, "按钮：读取并写入"),
    ('text="输入一个点后：TCP 用 IK 判断可达；关节点不做检查，输入合法后直接加入。只有 TCP 检查通过的点或合法关节点才会加入下面列表。"',
     'text="输入一个点后：法兰位姿用 IK 判断可达；关节点不做检查，输入合法后直接加入。只有法兰点检查通过的点或合法关节点才会加入下面列表。"',
     1, "标签：说明1"),
    ('text="已检查通过的连续运动点（按加入顺序执行，可混合 TCP / 关节点）"',
     'text="已检查通过的连续运动点（按加入顺序执行，可混合 法兰位姿 / 关节点）"', 1, "标签：列表标题"),
    ('text="执行：普通 TCP 首点 MoveJ、后续优先 MoveL；MoveL 失败直接用仿真已验证的 IK 解 MoveJ 兜底；末端特异点仅 J6 ±180°；关节点直接 MoveJ。实机不重复做轨迹预检。"',
     'text="执行：普通法兰点首点 MoveJ、后续优先 MoveL；MoveL 失败直接用已验证的 IK 解 MoveJ 兜底；末端特异点仅 J6 ±180°；关节点直接 MoveJ。实机不重复做轨迹预检。"',
     1, "标签：执行说明"),
    # 启动日志：加一条坐标基准说明
    ('log("单点：输入坐标 -> 检测可达性 -> 执行 MoveL/MoveJ")',
     'log("坐标基准：本脚本输入/显示/记录的都是【法兰】位姿（不含末端工具）；运动前自动 法兰×工具。当前工具 = %s" % pose_to_fanuc(robot.PoseTool())[:6])\n'
     'log("单点：输入法兰坐标 -> 检测可达性 -> 执行 MoveL/MoveJ")',
     1, "启动日志：坐标基准"),
    # ---- 第二轮：只改"给操作员看的"文案，内部标识（type="TCP"、kind=="TCP"、
    #      traj_type 的 value="TCP"）一律保留，避免破坏 JSON 兼容与逻辑判断 ----
    (r'log("TCP IK', r'log("法兰 IK', 4, "日志：IK 前缀"),
    ("的 TCP 连续 IK", "的法兰连续 IK", 1, "日志：连续IK标题"),
    ('log("  TCP：X=', 'log("  法兰：X=', 1, "日志：采样点"),
    ('"P%-3d [TCP]%s', '"P%-3d [法兰]%s', 1, "记录列表：标签"),
    ("[TCP-特异点]", "[法兰-特异点]", 2, "记录/日志：特异点"),
    ("普通 TCP 点", "普通法兰点", 5, "文案：普通点"),
    ("普通 TCP", "普通法兰", 12, "文案：普通"),
    ("该 TCP 点", "该法兰点", 1, "日志：未加入"),
    ("的路 TCP", "的路法兰", 0, "占位（不替换）"),
    ('log("P%d [TCP]', 'log("P%d [法兰]', 4, "日志：P%d 标签"),
    ('log("========== 读取当前法兰', 'log("========== 读取当前法兰', 1, "noop 校验"),
    ('log("单点：输入法兰坐标', 'log("单点：输入法兰坐标', 1, "noop 校验2"),
    ('log("目标关节：输入 J1~J6 -> 实机 MoveJ（不经过 TCP/Fanuc 转换和 IK）")',
     'log("目标关节：输入 J1~J6 -> 实机 MoveJ（不经过法兰换算/Fanuc 转换和 IK）")', 1, "启动日志：关节"),
    ('log("连续运动：支持导入仿真JSON；普通TCP使用仿真已验证IK（缺少时仅做单点SolveIK）；末端特异点跳过IK仅J6±180°；实机执行不重复轨迹预检；MoveL失败直接用仿真已验证IK解MoveJ兜底")',
     'log("连续运动：支持导入本脚本导出的JSON；普通法兰点使用已验证IK（缺少时仅做单点SolveIK）；末端特异点跳过IK仅J6±180°；实机执行不重复轨迹预检；MoveL失败直接用已验证IK解MoveJ兜底")',
     1, "启动日志：连续"),
]


def main():
    # 控制台是 GBK：强制 UTF-8 输出，避免打印 ⚠️ 之类字符时抛 UnicodeEncodeError
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    text = io.open(SRC, encoding="utf-8").read()
    print("source: %s  (%d chars)" % (SRC, len(text)))
    ok = True
    for old, new, expect, what in REPLACEMENTS:
        n = text.count(old)
        flag = "OK " if n == expect else "!! "
        print("  [%s] %-24s 命中 %d (期望 %d)" % (flag, what, n, expect))
        if n != expect:
            ok = False
            continue
        text = text.replace(old, new)
    if not ok:
        raise SystemExit("!! 有替换未按预期命中，未写出文件")

    io.open(DST, "w", encoding="utf-8", newline="\n").write(text)
    print("\nwrote %s (%d chars)" % (DST, len(text)))

    # 残留检查：还剩哪些 TCP 字样（应只剩"不经过 TCP"这类说明）
    print("\n=== 残留的 TCP 字样（逐条确认是否应保留）===")
    for i, line in enumerate(text.splitlines(), 1):
        if "TCP" in line:
            print("  %5d: %s" % (i, line.strip()[:120]))

    # 语法检查
    import ast
    ast.parse(text)
    print("\nsyntax OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
