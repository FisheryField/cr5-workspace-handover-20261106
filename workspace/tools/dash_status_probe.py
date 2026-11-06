#!/usr/bin/env python3
"""只读探针：报警 + 坐标系 + 位姿一致性。不发任何运动命令。"""
import socket
import sys
import time

HOST = "192.168.5.1"
CMDS = [
    "GetErrorID()",
    "RobotMode()",
    "GetAngle()",
    "GetPose()",
    "ToolFrame()",
    "UserFrame()",
    "SpeedFactor()",
    "GetRampTime()",
    "AO()",
]


def main():
    s = socket.create_connection((HOST, 29999), timeout=8)
    s.settimeout(5.0)
    for c in CMDS:
        if c == "AO()":
            continue
        t0 = time.time()
        try:
            s.sendall(c.encode("utf-8"))
            data = s.recv(1024)
        except Exception as e:
            data = ("<ERR %r>" % e).encode()
        print("[%-14s] <- %s (%.2f s)" % (c[:-2], data.decode("utf-8", "replace").strip(), time.time() - t0))
        time.sleep(0.15)
    s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
