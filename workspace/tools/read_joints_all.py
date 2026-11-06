#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读 30005 实时流，把所有 6×double 分组打印出来，找真正的关节角字段。只读。"""
import socket
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "192.168.5.1", 30005
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]


def main():
    s = socket.create_connection((HOST, PORT), timeout=8)
    buf = b""
    while len(buf) < 1440:
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
    s.close()
    print("收到 %d 字节" % len(buf))
    if len(buf) < 1440:
        return 2
    print("header u64x4:", struct.unpack_from("<4Q", buf, 0))
    for off in range(0, 1440 - 48 + 1, 8):
        vals = struct.unpack_from("<6d", buf, off)
        if all(abs(v) <= 400.0 for v in vals) and any(v != 0.0 for v in vals):
            print("off %4d : %s" % (off, "  ".join("%s=%10.5f" % (n, v) for n, v in zip(NAMES, vals))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
