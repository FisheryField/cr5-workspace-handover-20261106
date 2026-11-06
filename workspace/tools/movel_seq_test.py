#!/usr/bin/env python3
"""MoveJ(J6->180, J1~J5 冻结) -> MoveL(0,-441,947,-90,0,180) 连续执行，同一次连接。
用法: python tools/movel_seq_test.py
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
J6_TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
TARGET = ([float(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2
          else [0.0, -441.0, 947.0, -90.0, 0.0, 180.0])

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
                rows.append((time.time(),
                             struct.unpack_from("<6d", frame, 192),
                             struct.unpack_from("<6d", frame, 128)))
        s.close()
    except Exception as e:
        print("[sampler] %r" % e)


def fmt(v):
    return " ".join("%s=%+.3f" % (n, x) for n, x in zip(NAMES, v))


def snap(tag):
    if rows:
        _, qa, qt = rows[-1]
        print("  [%s] actual %s" % (tag, fmt(qa)))
    else:
        print("  [%s] no frame" % tag)


def main():
    RDK = Robolink()
    robot = RDK.Item('', ITEM_TYPE_ROBOT)
    if not robot.Valid():
        print("!! 未找到机器人")
        return 2
    q0 = [round(v, 3) for v in robot.SimulatorJoints()]
    print("[0] robot=%r ConnectedState=%r joints=%s" % (robot.Name(), robot.ConnectedState(), q0), flush=True)

    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    time.sleep(0.8)
    snap("before")

    robot.Connect()
    time.sleep(1.2)
    st, msg = robot.ConnectedState()
    print("[1] ConnectedState=%s %r" % (st, msg), flush=True)
    if st < 0:
        print("!! 未连接")
        stop_flag.set()
        return 3
    RDK.setRunMode(RUNMODE_RUN_ROBOT)
    robot.setPoseFrame(robot.PoseFrame())
    robot.setPoseTool(robot.PoseTool())
    robot.setSpeed(ROBOT_SPEED)

    # ---- 第一步: MoveJ J6 -> 180 (J1~J5 冻结) ----
    qa = list(robot.SimulatorJoints())
    qa[5] = J6_TARGET
    print("[2] MoveJ J6->%s (q=%s)" % (J6_TARGET, [round(v, 2) for v in qa]), flush=True)
    t0 = time.time()
    try:
        robot.MoveJ(qa)
        print("    MoveJ 正常 (%.2f s)" % (time.time() - t0))
    except Exception as e:
        print("    MoveJ %s: %s (%.2f s)" % (type(e).__name__, e, time.time() - t0))
    time.sleep(1.0)
    snap("after MoveJ")
    print("    GUI joints=%s" % [round(v, 3) for v in robot.SimulatorJoints()], flush=True)

    # ---- 第二步: MoveL 到目标 ----
    target = Fanuc_2_Pose(TARGET)
    print("[3] MoveL -> %s" % TARGET, flush=True)
    t0 = time.time()
    try:
        robot.MoveL(target)
        print("    MoveL 正常 (%.2f s)" % (time.time() - t0))
    except Exception as e:
        print("    MoveL %s: %s (%.2f s)" % (type(e).__name__, e, time.time() - t0))
    time.sleep(2.0)
    snap("after MoveL")

    try:
        q1 = [round(v, 3) for v in robot.SimulatorJoints()]
        p1 = Pose_2_Fanuc(robot.Pose())
        print("[4] joints=%s" % q1)
        print("    TCP: X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(p1[:6]))
        print("    与目标直线偏差 %.1f mm" % sqrt((p1[0]-TARGET[0])**2 + (p1[1]-TARGET[1])**2 + (p1[2]-TARGET[2])**2))
    except Exception as e:
        print("[4] 读位姿失败 %r" % e)

    try:
        RDK.setRunMode(RUNMODE_SIMULATE)
        print("[5] RunMode 恢复 SIMULATE")
    except Exception as e:
        print("[5] %r" % e)

    time.sleep(2.0)
    stop_flag.set()
    t.join(timeout=3)
    if rows:
        print("==== 采样 %d 帧 ====" % len(rows))
        for i, n in enumerate(NAMES):
            a = [r[1][i] for r in rows]
            print("%s %10.4f -> %10.4f (min %10.4f max %10.4f)" % (n, a[0], a[-1], min(a), max(a)))
        with open("_movel_seq_test.csv", "w", encoding="utf-8") as f:
            f.write("t," + ",".join("qa_%s" % n for n in NAMES) + ","
                    + ",".join("qt_%s" % n for n in NAMES) + "\n")
            t0 = rows[0][0]
            for ts, qaa, qtt in rows:
                f.write("%.3f," % (ts - t0) + ",".join("%.6f" % v for v in qaa) + ","
                        + ",".join("%.6f" % v for v in qtt) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
