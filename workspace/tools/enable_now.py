#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清报警 + 上使能（手臂已托住，仅做这一步，不运动）。

步骤：
  1) 读现状：RobotMode / GetAngle / GetErrorID
  2) 若 J2 伺服故障仍在 -> 写厂商参数 H0C.00(0x200C:01)=1 做驱动器故障复位
  3) ClearError()（控制器报警）
  4) SpeedFactor(5) / AccJ(5) -> EnableRobot()
  5) 读回：RobotMode / GetErrorID / GetAngle，并给出结论
不发任何运动指令。
"""
import json
import socket
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST, PORT = "192.168.5.1", 30003


def http_reset_j2():
    body = json.dumps({"body": [{"key": "addr200C01", "servoNum": "J2", "value": 1}]}).encode()
    req = urllib.request.Request("http://%s:22000/settings/modifyServoParams" % HOST, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return "HTTP %s %r" % (r.status, r.read()[:120])
    except urllib.error.HTTPError as exc:
        return "HTTPError %s %s" % (exc.code, exc.reason)
    except Exception as exc:  # noqa: BLE001
        return "EXC %s: %s" % (type(exc).__name__, exc)


class Bot:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=10)
        self.s.settimeout(5)

    def cmd(self, c, wait=0.6):
        self.s.sendall((c + "\n").encode())
        time.sleep(wait)
        try:
            return self.s.recv(16384).decode('utf-8', 'replace').strip()
        except socket.timeout:
            return "<no reply>"

    def angles(self):
        r = self.cmd("GetAngle()", 0.6)
        try:
            return [float(v) for v in r.split("{", 1)[1].split("}", 1)[0].split(",")]
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
        try:
            return json.loads(r.split("{", 1)[1].rsplit("}", 1)[0])
        except Exception:  # noqa: BLE001
            return r

    def close(self):
        self.s.close()


def fmt(a):
    return "  ".join("%+9.4f" % v for v in a) if a else "?"


def main():
    b = Bot()
    print("现状  mode=%s errors=%s" % (b.mode(), b.errors()))
    print("      GetAngle:", fmt(b.angles()))

    errs = b.errors()
    servo = errs[2] if isinstance(errs, list) and len(errs) > 2 else []
    if servo:
        print("J2 伺服故障仍在 %s -> 写 H0C.00=1 复位" % servo)
        print("      ->", http_reset_j2())
        time.sleep(1.5)
        print("      复位后 errors=%s" % (b.errors(),))
    else:
        print("J2 伺服故障当前为空，直接清控制器报警")

    print("ClearError() ->", b.cmd("ClearError()", 1.2))
    print("      mode=%s errors=%s" % (b.mode(), b.errors()))
    print("SpeedFactor(5) ->", b.cmd("SpeedFactor(5)", 0.7))
    print("AccJ(5)        ->", b.cmd("AccJ(5)", 0.7))

    print(">>> EnableRobot()  （手臂已托住）")
    print("      ->", b.cmd("EnableRobot()", 9.0))
    m, e, a = b.mode(), b.errors(), b.angles()
    print("      使能后 mode=%s" % m)
    print("      errors=%s" % (e,))
    print("      GetAngle:", fmt(a))
    if m == 5 and not (isinstance(e, list) and any(e)):
        print(">>> 使能成功且无报警：J2 伺服没有复现 33921")
    elif m == 5:
        print(">>> 已使能，但仍有报警条目：%s" % (e,))
    else:
        print(">>> 未进入使能状态（mode=%s），故障仍在" % m)
    b.close()


if __name__ == "__main__":
    main()
