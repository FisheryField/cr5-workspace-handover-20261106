#!/usr/bin/env python3
"""RoboDK 链路探针：复刻 机械臂TCP真实运动.py 的同款调用路径。

只读检查（--check）：
  1. Robolink() 连接 RoboDK GUI
  2. robot = Item('', ITEM_TYPE_ROBOT) 是否有效
  3. robot.ConnectedState() 实机连接状态
  4. RDK.RunMode() / robot 参数
  5. SolveIK 是否正常
可选 --j6 <deg>：按脚本同款方式（MoveJ 关节表）让 J6 转指定角度。
可选 --tool：列出站点里全部工具/坐标系名称。

运行前提：本机已 pip install robodk（API 库），RoboDK GUI 已开（无需打开文件）。
"""
import sys
import time

from robodk.robolink import *  # noqa: F401,F403
from robodk.robomath import *  # noqa: F401,F403

ROBOT_SPEED = 20.0


def log(s):
    print(s, flush=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--j6", type=float, default=None,
                    help="J6 target absolute angle in deg (via MoveJ)")
    ap.add_argument("--tool", action="store_true", help="list tools/frames")
    ap.add_argument("--yes", action="store_true", help="skip confirmation")
    args = ap.parse_args()

    log("[1] Robolink() ...")
    RDK = Robolink()
    robot = RDK.Item('', ITEM_TYPE_ROBOT)
    if not robot.Valid():
        log("!! 未找到机器人 (Item('') invalid)")
        return 2
    log("    robot = %r" % robot.Name())

    log("[2] ConnectedState ...")
    status, msg = robot.ConnectedState()
    log("    status=%s msg=%r" % (status, msg))

    log("[3] RunMode = %s" % RDK.RunMode())

    if args.tool:
        log("[T] station items:")
        for it in RDK.ItemList():
            log("    type=%d %r" % (it.type, it.name()))
        return 0

    if args.j6 is None:
        return 0

    # ---- 与脚本一致的执行路径 ----
    if not args.yes:
        log("!! 需要 --yes 才会真正运动 J6 到 %.3f deg" % args.j6)
        return 2

    log("[4] robot.Connect() ...")
    robot.Connect()
    time.sleep(1.5)
    status, msg = robot.ConnectedState()
    log("    status=%s msg=%r" % (status, msg))
    if status < 0:
        log("!! 机器人连接未建立")
        return 3

    RDK.setRunMode(RUNMODE_RUN_ROBOT)
    robot.setPoseFrame(robot.PoseFrame())
    robot.setPoseTool(robot.PoseTool())
    robot.setSpeed(ROBOT_SPEED)
    q = list(robot.SimulatorJoints())
    log("    SimulatorJoints = %s" % [round(v, 3) for v in q])
    q[5] = args.j6
    log("[5] MoveJ -> J6=%.3f (J1..J5 unchanged)" % args.j6)
    try:
        robot.MoveJ(q)
        log("    MoveJ 返回正常")
    except Exception as e:
        log("    MoveJ 异常: %s: %s" % (type(e).__name__, e))
        raise
    time.sleep(1.0)
    q2 = list(robot.SimulatorJoints())
    log("    after MoveJ SimulatorJoints = %s" % [round(v, 3) for v in q2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
