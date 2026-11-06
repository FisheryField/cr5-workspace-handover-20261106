#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""保守版回零：通过控制器 30003 口分小步把六轴送到 (0,0,0,0,0,0)。

保守点：
  * SpeedFactor 5%（失败则退 10%）
  * 分 N 小步（默认 10 步，单轴单步 ≤ ~7°），每步都等"到位"再走下一步
  * 每步之后检查 GetErrorID()，只要出现任何报警立刻停止
  * 每步之后检查 RobotMode()，一旦不是 5（使能）立刻停止
不做任何"重试/兜底"，出问题就停。
"""
import socket
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST, PORT = "192.168.5.1", 30003
N_STEPS = 10
SPEED_FACTOR = 5
ARRIVE_TOL = 0.3          # 单轴到位判据（度）
STEP_TIMEOUT = 45.0       # 单步最长等待
MODE_ENABLED = 5


class Bot:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=10)
        self.s.settimeout(5)

    def cmd(self, c, wait=0.5):
        self.s.sendall((c + "\n").encode())
        time.sleep(wait)
        try:
            return self.s.recv(16384).decode('utf-8', 'replace').strip()
        except socket.timeout:
            return "<no reply>"

    def angles(self):
        r = self.cmd("GetAngle()", 0.6)
        try:
            body = r.split("{", 1)[1].split("}", 1)[0]
            return [float(v) for v in body.split(",")]
        except Exception:  # noqa: BLE001
            return None

    def mode(self):
        r = self.cmd("RobotMode()", 0.6)
        try:
            return int(r.split("{", 1)[1].split("}", 1)[0])
        except Exception:  # noqa: BLE001
            return None

    def errors(self):
        r = self.cmd("GetErrorID()", 0.8)
        nums = [int(x) for x in __import__("re").findall(r"\d+", r.split("{", 1)[-1])]
        return nums

    def close(self):
        self.s.close()


def fmt(a):
    return "  ".join("%+9.4f" % v for v in a)


def main():
    b = Bot()
    a0 = b.angles()
    print("起点 GetAngle :", fmt(a0), " RobotMode:", b.mode(), " errors:", b.errors())
    if a0 is None:
        print("读不到当前角度，放弃"); return

    print("ClearError()  ->", b.cmd("ClearError()", 1.0))
    print("SpeedFactor(%d) ->" % SPEED_FACTOR, b.cmd("SpeedFactor(%d)" % SPEED_FACTOR, 0.8))
    print("AccJ(5)       ->", b.cmd("AccJ(5)", 0.8))
    print(">>> EnableRobot()")
    print("    ->", b.cmd("EnableRobot()", 8.0))
    print("RobotMode:", b.mode(), " errors:", b.errors())
    a1 = b.angles()
    print("使能后 GetAngle:", fmt(a1), "(与起点之差 %s)" %
          ("  ".join("%+.4f" % (x - y) for x, y in zip(a1, a0)) if a1 else "-"))
    if b.mode() != MODE_ENABLED:
        print("!! 未进入使能状态（mode=%s），停止" % b.mode())
        b.close(); return

    target_all = [0.0] * 6
    cur = a1
    for k in range(1, N_STEPS + 1):
        step = [c + (t - c) * k / float(N_STEPS) for c, t in zip(a0, target_all)]
        print("---- 步 %2d/%d 目标: %s" % (k, N_STEPS, fmt(step)))
        print("     JointMovJ ->", b.cmd("JointMovJ(%.4f,%.4f,%.4f,%.4f,%.4f,%.4f)" % tuple(step), 0.8))
        t0 = time.time()
        while time.time() - t0 < STEP_TIMEOUT:
            a = b.angles()
            if a:
                err = max(abs(x - y) for x, y in zip(a, step))
                if err < ARRIVE_TOL:
                    break
            time.sleep(0.8)
        else:
            a = b.angles()
            print("     !! 步 %d 在 %.0fs 内未到位，实测 %s" % (k, STEP_TIMEOUT, fmt(a) if a else "?"))
            print("     !! 停止（不做兜底）")
            break
        errs = b.errors()
        m = b.mode()
        print("     到位 %s   mode=%s errors=%s" % (fmt(a), m, errs))
        if errs:
            print("     !! 出现报警，停止"); break
        if m != MODE_ENABLED:
            print("     !! 机器人不再处于使能状态（mode=%s），停止" % m); break
        cur = a
    print("最终 GetAngle:", fmt(b.angles() or [0] * 6))
    print("最终 RobotMode:", b.mode(), " errors:", b.errors())
    b.close()


if __name__ == "__main__":
    main()
