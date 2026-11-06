#!/usr/bin/env python3
"""Dump the whole 1440-byte CR5 feedback packet and query the dashboard.

Two independent sources, so the joint values are not a guess:
  A) port 30005 realtime stream, every 8-byte-aligned float64 printed
  B) port 29999 dashboard, ASCII command (TryGetAngle / GetAngle / RobotMode)
"""
import socket
import struct
import sys
import time

HOST = "192.168.5.1"


def stream():
    s = socket.create_connection((HOST, 30005), timeout=8)
    buf = b""
    while len(buf) < 1440:
        c = s.recv(4096)
        if not c:
            break
        buf += c
    s.close()
    print("=" * 70)
    print("A) port 30005 packet: %d bytes" % len(buf))
    print("=" * 70)
    print("  header u64 x4 : %s" % (struct.unpack_from("<4Q", buf, 0),))
    print()
    n = len(buf) // 8
    print("  all %d float64 values (only rows containing a nonzero are shown):" % n)
    for i in range(n):
        row = struct.unpack_from("<6d", buf, i * 8) if (i + 6) * 8 <= len(buf) else None
        if row is None:
            break
        if any(abs(v) > 1e-9 for v in row):
            print("    [%3d] (%4d..%4d) : %s"
                  % (i, i * 8, i * 8 + 47,
                     "  ".join("%12.6f" % v for v in row)))


def dashboard():
    print()
    print("=" * 70)
    print("B) port 29999 dashboard")
    print("=" * 70)
    try:
        s = socket.create_connection((HOST, 29999), timeout=6)
    except Exception as e:
        print("  connect failed: %s" % e)
        return
    s.settimeout(3)
    time.sleep(0.3)
    try:
        s.recv(4096)          # banner, if any
    except Exception:
        pass
    for cmd in ("RobotMode()", "GetAngle()", "GetPose()"):
        try:
            s.sendall((cmd + "\n").encode())
            time.sleep(0.6)
            s.settimeout(2.5)
            try:
                r = s.recv(4096).decode("utf-8", "replace").strip()
            except socket.timeout:
                r = "(no reply / timeout)"
            print("  %-14s -> %s" % (cmd, r))
        except Exception as e:
            print("  %-14s -> ERROR %s" % (cmd, e))
    s.close()


if __name__ == "__main__":
    stream()
    dashboard()
