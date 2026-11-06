#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：从 30004/30005 反馈流里找"关节位姿"字段，并与已知的驱动器上报位姿比对。
反馈口由 gcontrol 提供，和 29999/30003 的"控制模式"无关，因此当前仍可用。"""
import socket
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DRIVE = [65.763704, 95.066674, -32.999036, -6.095176, -65.570506, -0.008733]   # 10:28 (PDO) 列
MODEL = [65.769586, 95.035484, -3.370089, 20.835418, -65.567655, -0.009268]    # 10:28 nextPos 列


def grab(port, n=1440):
    s = socket.create_connection(("192.168.5.1", port), timeout=8)
    buf = b""
    while len(buf) < n:
        c = s.recv(8192)
        if not c:
            break
        buf += c
    s.close()
    return buf


def show(port):
    buf = grab(port)
    print("=== port %d : %d bytes ===" % (port, len(buf)))
    if len(buf) < 1440:
        print("  短包，跳过")
        return
    hits = []
    for off in range(0, 1440 - 48 + 1, 8):
        v = struct.unpack_from("<6d", buf, off)
        if all(abs(x) <= 400 for x in v) and sum(1 for x in v if x != 0.0) >= 4:
            tag = ""
            if all(abs(a - b) < 1.0 for a, b in zip(v, DRIVE)):
                tag = "   <<== 驱动器上报位姿"
            elif all(abs(a - b) < 1.0 for a, b in zip(v, MODEL)):
                tag = "   <<== 旧的模型位姿(10:28)"
            hits.append((off, v, tag))
    for off, v, tag in hits:
        print("  off %4d : %s%s" % (off, "  ".join("%+10.5f" % x for x in v), tag))
    if not hits:
        print("  没有找到像关节位姿的 6×double 字段")


show(30005)
show(30004)
