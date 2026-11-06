#!/usr/bin/env python3
"""复现「只响应一次」：同款路径连续两次 MoveJ（不重连）+ 第三次重连后 MoveJ。

安全边界：只动 J6（J1..J5 冻结在当前值），速度 20，与用户脚本/j6_move_test 相同。
四路证据：
  A. RoboDK SimulatorJoints（GUI 模型）
  B. 30005 q_target / q_actual（字节 192+8i / 128+8i，b32 仅留对照）
  C. 每步前后 ConnectedState / RunMode
  D. 驱动侧响应（MoveJ 是否正常返回）
用法: python tools/j6_twice_test.py [j6_abs_deg]   默认 current+180
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
                qa = struct.unpack_from("<6d", frame, 192)
                qt = struct.unpack_from("<6d", frame, 128)
                rows.append((time.time(), qa, qt))
        s.close()
    except Exception as e:
        print("[sampler] error: %r" % e)


def snap(tag):
    if rows:
        t, qa, qt = rows[-1]
        print("  [%s] actual %s" % (tag, " ".join("%s=%+.4f" % (n, v) for n, v in zip(NAMES, qa))))
        print("  [%s] target %s" % (tag, " ".join("%s=%+.4f" % (n, v) for n, v in zip(NAMES, qt))))
    else:
        print("  [%s] no frame" % tag)


def movej_j6(robot, j6_target, label):
    q = list(robot.SimulatorJoints())
    q[5] = j6_target
    print("  [%s] MoveJ -> %s" % (label, [round(v, 3) for v in q]), flush=True)
    t0 = time.time()
    try:
        robot.MoveJ(q)
        print("  [%s] MoveJ 返回正常 (耗时 %.2f s)" % (label, time.time() - t0))
        return True
    except Exception as e:
        print("  [%s] MoveJ 异常: %s: %s (耗时 %.2f s)" % (label, type(e).__name__, e, time.time() - t0))
        return False


def main():
    print("[0] 连接 RoboDK ...", flush=True)
    RDK = Robolink()
    robot = RDK.Item('', ITEM_TYPE_ROBOT)
    if not robot.Valid():
        print("!! 未找到机器人")
        return 2
    print("    robot = %r" % robot.Name())
    st, msg = robot.ConnectedState()
    print("    ConnectedState(前): %s %r  RunMode=%s" % (st, msg, RDK.RunMode()))
    q_rdk0 = [round(v, 4) for v in robot.SimulatorJoints()]
    print("    SimulatorJoints(before): %s" % q_rdk0)

    if len(sys.argv) > 1:
        j6_a = float(sys.argv[1])
    else:
        j6_a = q_rdk0[5] + 180.0
    j6_a = ((j6_a + 180.0) % 360.0) - 180.0
    if j6_a <= -180.0:
        j6_a = 180.0
    j6_b = q_rdk0[5]  # 回到起点 => 两次相反方向各 180
    print("[1] 目标: 第一次 MoveJ J6 -> %+.3f；第二次 MoveJ J6 -> %+.3f (回起点)" % (j6_a, j6_b))

    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    time.sleep(1.0)
    snap("before")

    print("[2] robot.Connect() ...", flush=True)
    robot.Connect()
    time.sleep(1.5)
    st, msg = robot.ConnectedState()
    print("    ConnectedState(连接后): %s %r" % (st, msg))
    RDK.setRunMode(RUNMODE_RUN_ROBOT)
    robot.setPoseFrame(robot.PoseFrame())
    robot.setPoseTool(robot.PoseTool())
    robot.setSpeed(ROBOT_SPEED)

    ok1 = movej_j6(robot, j6_a, "第1次")
    time.sleep(2.0)
    snap("after#1")
    st, msg = robot.ConnectedState()
    print("    ConnectedState(#1后): %s %r" % (st, msg))

    ok2 = movej_j6(robot, j6_b, "第2次(不重连)")
    time.sleep(2.0)
    snap("after#2")
    st, msg = robot.ConnectedState()
    print("    ConnectedState(#2后): %s %r" % (st, msg))

    if not ok2:
        print("[3] 第2次失败 -> 重新 robot.Connect() 后再试")
        robot.Connect()
        time.sleep(1.5)
        st, msg = robot.ConnectedState()
        print("    ConnectedState(重连后): %s %r" % (st, msg))
        RDK.setRunMode(RUNMODE_RUN_ROBOT)
        movej_j6(robot, j6_a, "第3次(重连后)")
        time.sleep(2.0)
        snap("after#3")

    time.sleep(3.0)
    stop_flag.set()
    t.join(timeout=3)
    snap("final")
    q_rdk1 = [round(v, 4) for v in robot.SimulatorJoints()]
    print("[4] SimulatorJoints(final): %s" % q_rdk1)

    try:
        RDK.setRunMode(RUNMODE_SIMULATE)
        print("[5] RunMode 已恢复 RUNMODE_SIMULATE")
    except Exception as e:
        print("[5] 恢复 RunMode 失败: %r" % e)

    if rows:
        print("\n==== 30005 采样汇总 (%d 帧) ====" % len(rows))
        for i, n in enumerate(NAMES):
            a = [r[1][i] for r in rows]
            tt = [r[2][i] for r in rows]
            print("%s actual %10.4f -> %10.4f (min %10.4f max %10.4f) | target %10.4f -> %10.4f"
                  % (n, a[0], a[-1], min(a), max(a), tt[0], tt[-1]))
        with open("_j6_twice_test.csv", "w", encoding="utf-8") as f:
            f.write("t," + ",".join("qa_%s" % n for n in NAMES) + ","
                    + ",".join("qt_%s" % n for n in NAMES) + "\n")
            t0 = rows[0][0]
            for ts, qa, qt in rows:
                f.write("%.3f," % (ts - t0) + ",".join("%.6f" % v for v in qa) + ","
                        + ",".join("%.6f" % v for v in qt) + "\n")
        print("csv -> _j6_twice_test.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
