#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过控制器 30003（gcontrol 命令口）把六轴 JointMovJ 回零。与 RoboDK 无关。

流程：RobotMode/GetAngle 现状 → ClearError → EnableRobot → SpeedFactor(10%)
      → JointMovJ(0,0,0,0,0,0) → 轮询 GetAngle 直到六轴都 ≈0（或超时）
只发这一条运动指令，不做任何其它动作。
"""
import socket
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST, PORT = "192.168.5.1", 30003
TARGET = [0.0] * 6
SPEED_FACTOR = 10          # 首次回零用 10%（用户脚本平时用 20%）
TOL = 0.05
TIMEOUT_S = 120.0


class Bot:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=10)
        self.s.settimeout(5)

    def cmd(self, c, wait=0.5):
        self.s.sendall((c + "\n").encode())
        time.sleep(wait)
        try:
            return self.s.recv(8192).decode('utf-8', 'replace').strip()
        except socket.timeout:
            return "<no reply>"

    def angles(self):
        r = self.cmd("GetAngle()", 0.6)
        try:
            body = r.split("{", 1)[1].split("}", 1)[0]
            return [float(v) for v in body.split(",")]
        except Exception:  # noqa: BLE001
            return None

    def close(self):
        self.s.close()


def main():
    b = Bot()
    print("RobotMode()      ->", b.cmd("RobotMode()", 0.6))
    a0 = b.angles()
    print("GetAngle() now   ->", a0)

    print("ClearError()     ->", b.cmd("ClearError()", 1.0))
    print("EnableRobot()    ->", b.cmd("EnableRobot()", 6.0))
    print("RobotMode()      ->", b.cmd("RobotMode()", 0.6))
    print("SpeedFactor(%d)  ->" % SPEED_FACTOR, b.cmd("SpeedFactor(%d)" % SPEED_FACTOR, 0.6))
    a1 = b.angles()
    print("GetAngle() armed ->", a1)

    print(">>> JointMovJ(0,0,0,0,0,0)")
    print("    ->", b.cmd("JointMovJ(0,0,0,0,0,0)", 1.0))

    t0 = time.time()
    last = None
    while time.time() - t0 < TIMEOUT_S:
        a = b.angles()
        if a is None:
            print("   [%5.1fs] GetAngle 解析失败" % (time.time() - t0))
            time.sleep(1.0)
            continue
        if a != last:
            print("   [%5.1fs] %s" % (time.time() - t0, "  ".join("%+9.4f" % v for v in a)))
            last = a
        if max(abs(v) for v in a) < TOL:
            print(">>> 已回到零点附近（全部 |角| < %.2f°），用时 %.1fs" % (TOL, time.time() - t0))
            break
        time.sleep(1.0)
    else:
        print(">>> 超时 %.0fs 未收敛到零点" % TIMEOUT_S)

    print("RobotMode()      ->", b.cmd("RobotMode()", 0.6))
    print("GetAngle() final ->", b.angles())
    b.close()


if __name__ == "__main__":
    main()
