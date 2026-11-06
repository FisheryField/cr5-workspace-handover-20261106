#!/usr/bin/env python3
"""J6 +180 实机试验（复刻 机械臂TCP真实运动.py 同款路径）+ 30005 全程采样。

四路证据:
  A. RoboDK SimulatorJoints (GUI 侧模型, 由驱动反馈刷新)
  B. 30005 q_target  (gcontrol 指令值)
  C. 30005 q_actual  (主控上报的物理反馈)
  D. 运动前后 all/log 增量里的 FollowError (另步 grep)

用法: python tools/j6_move_test.py [j6_abs_deg]   (默认 current+180)
"""
import socket
import struct
import sys
import threading
import time

from robodk.robolink import *  # noqa: F401,F403
from robodk.robomath import *  # noqa: F401,F403

HOST, PORT = "192.168.5.1", 30005
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]
ROBOT_SPEED = 20.0

stop_flag = threading.Event()
rows = []


def sampler():
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
        buf = b""
        while not stop_flag.is_set():
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            while len(buf) >= 1440:
                frame, buf = buf[:1440], buf[1440:]
                qa = struct.unpack_from("<6d", frame, 32)
                qt = struct.unpack_from("<6d", frame, 128)
                rows.append((time.time(), qa, qt))
        s.close()
    except Exception as e:
        print("[sampler] error: %r" % e)


def snap(rows_local, tag):
    if rows_local:
        t, qa, qt = rows_local[-1]
        print("  [%s] actual %s" % (tag, " ".join("%s=%+.4f" % (n, v) for n, v in zip(NAMES, qa))))
        print("  [%s] target %s" % (tag, " ".join("%s=%+.4f" % (n, v) for n, v in zip(NAMES, qt))))
    else:
        print("  [%s] no frame" % tag)


def main():
    print("[0] 连接 RoboDK ...", flush=True)
    RDK = Robolink()
    robot = RDK.Item('', ITEM_TYPE_ROBOT)
    if not robot.Valid():
        print("!! 未找到机器人")
        return 2
    print("    robot = %r" % robot.Name())
    st, msg = robot.ConnectedState()
    print("    ConnectedState: %s %r" % (st, msg))
    q_rdk0 = [round(v, 4) for v in robot.SimulatorJoints()]
    print("    SimulatorJoints(before): %s" % q_rdk0)

    # 目标 J6 = 当前 + 180 (或命令行绝对值)
    if len(sys.argv) > 1:
        j6_target = float(sys.argv[1])
    else:
        j6_target = q_rdk0[5] + 180.0
    j6_target = ((j6_target + 180.0) % 360.0) - 180.0
    if j6_target <= -180.0:
        j6_target = 180.0
    print("[1] 目标: J6 %+.4f -> %+.4f (J1~J5 冻结)" % (q_rdk0[5], j6_target))

    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    time.sleep(1.0)
    n_before = len(rows)
    snap(rows, "before")

    print("[2] robot.Connect() ...", flush=True)
    robot.Connect()
    time.sleep(1.5)
    st, msg = robot.ConnectedState()
    print("    ConnectedState: %s %r" % (st, msg))

    try:
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        robot.setPoseFrame(robot.PoseFrame())
        robot.setPoseTool(robot.PoseTool())
        robot.setSpeed(ROBOT_SPEED)
        q = list(robot.SimulatorJoints())
        q[5] = j6_target
        print("[3] MoveJ -> %s" % [round(v, 3) for v in q], flush=True)
        t0 = time.time()
        try:
            robot.MoveJ(q)
            print("    MoveJ 返回正常 (耗时 %.2f s)" % (time.time() - t0))
        except Exception as e:
            print("    MoveJ 异常: %s: %s (耗时 %.2f s)" % (type(e).__name__, e, time.time() - t0))
    finally:
        # 观察窗口: 运动结束后再采样 5 s
        time.sleep(5.0)
        stop_flag.set()
        t.join(timeout=3)
        snap(rows, "after")

    q_rdk1 = [round(v, 4) for v in robot.SimulatorJoints()]
    print("[4] SimulatorJoints(after): %s" % q_rdk1)

    # 恢复仿真模式，避免 RoboDK 里后续误操作直发实机
    try:
        RDK.setRunMode(RUNMODE_SIMULATE)
        print("[5] RunMode 已恢复 RUNMODE_SIMULATE")
    except Exception as e:
        print("[5] 恢复 RunMode 失败: %r" % e)

    # ---- 采样汇总 ----
    if rows:
        print("\n==== 30005 采样汇总 (%d 帧) ====" % len(rows))
        for i, n in enumerate(NAMES):
            a = [r[1][i] for r in rows]
            tt = [r[2][i] for r in rows]
            print("%s actual first %10.4f last %10.4f min %10.4f max %10.4f | target first %10.4f last %10.4f min %10.4f max %10.4f"
                  % (n, a[0], a[-1], min(a), max(a), tt[0], tt[-1], min(tt), max(tt)))
        with open("_j6_move_test.csv", "w", encoding="utf-8") as f:
            f.write("t," + ",".join("qa_%s" % n for n in NAMES) + ","
                    + ",".join("qt_%s" % n for n in NAMES) + "\n")
            t0 = rows[0][0]
            for ts, qa, qt in rows:
                f.write("%.3f," % (ts - t0) + ",".join("%.6f" % v for v in qa) + ","
                        + ",".join("%.6f" % v for v in qt) + "\n")
        print("csv -> _j6_move_test.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
