# -*- coding: utf-8 -*-
"""通过 Dobot TCP 29999 仪表盘协议只读查询版本/状态。"""
import socket, sys

HOST = "192.168.5.1"
for cmd in ["Version()", "RobotMode()", "GetPose()"]:
    try:
        s = socket.create_connection((HOST, 29999), timeout=5)
        s.settimeout(5)
        banner = b""
        try:
            banner = s.recv(256)
        except Exception:
            pass
        s.sendall((cmd + "\n").encode())
        data = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 4096:
                    break
        except Exception:
            pass
        s.close()
        print(f"### {cmd}")
        if banner:
            print("   banner:", banner.decode("utf-8", "replace").strip()[:120])
        print("   reply :", data.decode("utf-8", "replace").strip()[:200] or "(空)")
    except Exception as e:
        print(f"### {cmd} -> {type(e).__name__}: {e}")
