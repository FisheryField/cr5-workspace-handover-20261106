#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CR5 控制器 29999 端口（Dashboard / API）命令行小工具。

用法：
    python tools/robot_cmd.py "RobotMode()" "GetAngle()" "SpeedFactor()"
每个参数是一条命令，按顺序发送，打印原始应答。
只做"发命令 → 打印应答"，不做任何等待/重试策略上的花活。
"""
import socket
import sys
import time

HOST, PORT = "192.168.5.1", 29999


def run(cmds, timeout=15.0, gap=0.4):
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    s.settimeout(timeout)
    try:
        for c in cmds:
            s.sendall((c + "\n").encode("utf-8"))
            time.sleep(gap)
            try:
                data = s.recv(65536)
            except socket.timeout:
                data = b"<timeout, no reply>"
            print(">>> %s" % c)
            print("    %r" % data.decode("utf-8", "replace").strip())
    finally:
        s.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        args = ["RobotMode()", "GetAngle()", "SpeedFactor()", "GetPose()"]
    run(args)
