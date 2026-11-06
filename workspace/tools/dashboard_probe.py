#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CR5 Dashboard(29999) 探针：先看有没有 banner，再发只读命令。"""
import socket
import sys
import time

HOST = "192.168.5.1"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def probe(port, cmds, timeout=10.0):
    print("=== port %d ===" % port)
    try:
        s = socket.create_connection((HOST, port), timeout=timeout)
    except Exception as exc:
        print("  连接失败: %s: %s" % (type(exc).__name__, exc))
        return
    s.settimeout(timeout)
    time.sleep(0.5)
    # 先看有没有主动推来的东西（banner / 实时流）
    try:
        first = s.recv(4096)
        print("  banner/首次接收 %d 字节: %r" % (len(first), first[:80]))
    except socket.timeout:
        print("  banner: 无（超时）")
    for c in cmds:
        try:
            s.sendall((c + "\n").encode("utf-8"))
        except Exception as exc:
            print("  发送 %s 失败: %s: %s" % (c, type(exc).__name__, exc))
            break
        time.sleep(0.6)
        try:
            data = s.recv(65536)
        except socket.timeout:
            data = b"<timeout>"
        except Exception as exc:
            print("  %s -> 接收异常 %s: %s" % (c, type(exc).__name__, exc))
            break
        if not data:
            print("  %s -> 对端关闭连接（空应答）" % c)
            break
        print("  %s -> %r" % (c, data.decode("utf-8", "replace").strip()[:200]))
    s.close()


if __name__ == "__main__":
    probe(29999, ["RobotMode()", "GetAngle()", "SpeedFactor()"])
    probe(30004, ["RobotMode()"])
