#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enable the robot over the Dobot dashboard port and, if it stays enabled,
run the vendor zero calibration (POST /calibrate/home on codesyscontrol:22000).

Read-only w.r.t. firmware; the only real effect is the calibration itself,
which is the intended step (the arm has not moved since the 15:01 calibration,
so the zero reference is reproduced).
"""
import socket
import sys
import time
import urllib.request

HOST = "192.168.5.1"


def dash(cmd, wait=0.8):
    s = socket.create_connection((HOST, 29999), timeout=8)
    s.settimeout(2.0)
    try:
        s.recv(4096)                      # banner, if any
    except socket.timeout:
        pass
    s.sendall((cmd + "\n").encode())
    time.sleep(wait)
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
            if len(c) < 4096:
                break
    except socket.timeout:
        pass
    s.close()
    return out.decode("utf-8", "replace").strip()


def post(path, body=b"{}"):
    req = urllib.request.Request("http://%s:22000%s" % (HOST, path), data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")[:200]


def main():
    print("RobotMode()  -> %r" % dash("RobotMode()"))
    print("EnableRobot()-> %r" % dash("EnableRobot()", wait=1.5))
    time.sleep(6)
    print("RobotMode()  -> %r" % dash("RobotMode()"))
    print("GetPose()    -> %r" % dash("GetPose()"))
    print()
    print("calibrate    -> %s" % (post("/calibrate/home"),))
    for i in (2, 4, 6, 8):
        time.sleep(2)
        print("  +%ds RobotMode() -> %r" % (i, dash("RobotMode()")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
