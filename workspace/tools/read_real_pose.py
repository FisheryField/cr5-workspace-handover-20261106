#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立读取真机位置（不使能、不运动）：
   1) 30004/30005 反馈流
   2) HTTP /interface/readCurrentEncoder （编码器只读）
用来和 GetAngle()（控制器上报/模型）对比。"""
import json
import socket
import struct
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = "192.168.5.1"
SCALE = 360.0 / (20000 * 101)


def stream(port, n=1440):
    try:
        s = socket.create_connection((HOST, port), timeout=6)
        buf = b""
        while len(buf) < n:
            c = s.recv(8192)
            if not c:
                break
            buf += c
        s.close()
    except Exception as exc:  # noqa: BLE001
        print("  port %d: EXC %s: %s" % (port, type(exc).__name__, exc))
        return
    print("  port %d: %d bytes" % (port, len(buf)))
    if len(buf) < 48:
        return
    for off in range(0, min(len(buf), 1440) - 48 + 1, 8):
        v = struct.unpack_from("<6d", buf, off)
        if all(abs(x) <= 400 for x in v) and sum(1 for x in v if x != 0.0) >= 4:
            print("    off %4d : %s" % (off, "  ".join("%+10.5f" % x for x in v)))


def http(path, body=None):
    url = "http://%s:22000%s" % (HOST, path)
    data = json.dumps(body).encode() if body is not None else b"{}"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print("  %-34s -> HTTP %s  %s" % (path, r.status, r.read()[:300].decode("utf-8", "replace")))
    except urllib.error.HTTPError as exc:
        print("  %-34s -> HTTPError %s %s" % (path, exc.code, exc.reason))
    except Exception as exc:  # noqa: BLE001
        print("  %-34s -> EXC %s: %s" % (path, type(exc).__name__, exc))


print("=== 30004/30005 反馈流 ===")
stream(30004)
stream(30005)
print("=== HTTP 只读路由 ===")
for p in ("/interface/readCurrentEncoder", "/interface/readCurrentEncoders",
          "/interface/getAngle", "/interface/robotStatus"):
    http(p)
print("scale: 1 count = %.9f deg" % SCALE)
