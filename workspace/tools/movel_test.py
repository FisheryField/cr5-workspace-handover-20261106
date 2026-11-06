#!/usr/bin/env python3
"""MoveL(TCP) 实机试验：复刻 机械臂TCP真实运动.py execute_single 的同款路径。

与用户脚本逐步一致：
  fanuc_to_pose(x,y,z,rx,ry,rz) -> SolveIK(tool, frame) 预检
  -> ensure_connected (Connect + sleep1.5 + ConnectedState + RUNMODE_RUN_ROBOT)
  -> setPoseFrame/setPoseTool/setSpeed(20) -> robot.MoveL(target)

不 MoveJ 兜底：MoveL 的任何异常都原样记录（这正是要取证的对象）。
证据：30005 b192(q_actual)/b128 采样 + RoboDK GUI joints/pose + API 返回。

用法: python tools/movel_test.py x,y,z,rx,ry,rz
默认: 0,-441,947,-90,0,180
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


def fmt(v):
    return " ".join("%s=%+.4f" % (n, x) for n, x in zip(NAMES, v))


def snap(tag):
    if rows:
        t, qa, qt = rows[-1]
        print("  [%s] actual %s" % (tag, fmt(qa)))
        print("  [%s] target %s" % (tag, fmt(qt)))
    else:
        print("  [%s] no frame" % tag)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "0,-441,947,-90,0,180"
    vals = [float(v.strip()) for v in arg.split(",")]
    if len(vals) < 6:
        print("!! 需要 6 个值")
        return 2
    x, y, z, rx, ry, rz = vals[:6]

    print("[0] 连接 RoboDK ...", flush=True)
    RDK = Robolink()
    robot = RDK.Item('', ITEM_TYPE_ROBOT)
    if not robot.Valid():
        print("!! 未找到机器人")
        return 2
    print("    robot=%r ConnectedState=%r RunMode=%s" %
          (robot.Name(), robot.ConnectedState(), RDK.RunMode()))
    q0 = [round(v, 4) for v in robot.SimulatorJoints()]
    print("    SimulatorJoints(before): %s" % q0)
    p0 = Pose_2_Fanuc(robot.Pose())
    print("    当前 TCP(Fanuc): X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(p0[:6]))

    target = Fanuc_2_Pose([x, y, z, rx, ry, rz])
    print("[1] 目标 TCP(Fanuc): X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % (x, y, z, rx, ry, rz))
    dist = sqrt((x - p0[0])**2 + (y - p0[1])**2 + (z - p0[2])**2)
    print("    与当前 TCP 直线距离 ≈ %.1f mm (speed=%.0f 预计 ≥%.1f s)" % (dist, ROBOT_SPEED, dist / ROBOT_SPEED))

    # ---- IK 预检（与脚本一致）----
    try:
        joints = robot.SolveIK(target, tool=robot.PoseTool(), reference=robot.PoseFrame())
        if joints is None:
            print("!! IK 不可达，取消")
            return 3
        q_ik = joints.list()
        if len(q_ik) < 6:
            print("!! IK 关节数异常: %r，取消" % q_ik)
            return 3
        print("[2] IK 可达: %s" % [round(v, 3) for v in q_ik[:6]])
    except Exception as e:
        print("[2] IK 检查失败: %s: %s" % (type(e).__name__, e))
        return 3

    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    time.sleep(1.0)
    snap("before")

    # ---- ensure_connected 同款 ----
    print("[3] robot.Connect() ...", flush=True)
    robot.Connect()
    time.sleep(1.5)
    st, msg = robot.ConnectedState()
    print("    ConnectedState: %s %r" % (st, msg))
    if st < 0:
        print("!! 连接未建立，取消")
        stop_flag.set()
        return 4
    RDK.setRunMode(RUNMODE_RUN_ROBOT)
    print("    RunMode: %s" % RDK.RunMode())

    try:
        robot.setPoseFrame(robot.PoseFrame())
        robot.setPoseTool(robot.PoseTool())
        robot.setSpeed(ROBOT_SPEED)
        print("[4] 发送 MoveL ...", flush=True)
        t0 = time.time()
        try:
            robot.MoveL(target)
            print("    MoveL 返回正常 (耗时 %.2f s)" % (time.time() - t0))
        except Exception as e:
            print("    MoveL 异常: %s: %s (耗时 %.2f s)" % (type(e).__name__, e, time.time() - t0))
    finally:
        time.sleep(5.0)
        stop_flag.set()
        t.join(timeout=3)
        snap("after")

    q1 = [round(v, 4) for v in robot.SimulatorJoints()]
    print("[5] SimulatorJoints(after): %s" % q1)
    try:
        p1 = Pose_2_Fanuc(robot.Pose())
        print("    之后 TCP(Fanuc): X=%.3f Y=%.3f Z=%.3f Rx=%.3f Ry=%.3f Rz=%.3f" % tuple(p1[:6]))
        print("    与目标差: dX=%.3f dY=%.3f dZ=%.3f (直线偏差 %.1f mm)" %
              (p1[0] - x, p1[1] - y, p1[2] - z,
               sqrt((p1[0] - x)**2 + (p1[1] - y)**2 + (p1[2] - z)**2)))
    except Exception as e:
        print("    读取之后 TCP 失败: %r" % e)

    try:
        RDK.setRunMode(RUNMODE_SIMULATE)
        print("[6] RunMode 已恢复 RUNMODE_SIMULATE")
    except Exception as e:
        print("[6] 恢复 RunMode 失败: %r" % e)

    if rows:
        print("\n==== 30005 采样汇总 (%d 帧) ====" % len(rows))
        for i, n in enumerate(NAMES):
            a = [r[1][i] for r in rows]
            tt = [r[2][i] for r in rows]
            print("%s actual %10.4f -> %10.4f (min %10.4f max %10.4f span %9.5f) | target %10.4f -> %10.4f (max %10.4f)"
                  % (n, a[0], a[-1], min(a), max(a), max(a) - min(a), tt[0], tt[-1], max(tt)))
        with open("_movel_test.csv", "w", encoding="utf-8") as f:
            f.write("t," + ",".join("qa_%s" % n for n in NAMES) + ","
                    + ",".join("qt_%s" % n for n in NAMES) + "\n")
            t0 = rows[0][0]
            for ts, qa, qt in rows:
                f.write("%.3f," % (ts - t0) + ",".join("%.6f" % v for v in qa) + ","
                        + ",".join("%.6f" % v for v in qt) + "\n")
        print("csv -> _movel_test.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
