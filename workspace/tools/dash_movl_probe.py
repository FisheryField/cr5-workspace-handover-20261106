#!/usr/bin/env python3
"""29999 直连重放驱动同款 MovL，抓控制器应答原文。
先读 GetAngle/GetPose/SpeedFactor（只读），再发 MovL(0,-441,947,-90,0,180)。
同时 30005 采样，判定物理是否运动。
"""
import socket
import struct
import sys
import threading
import time

HOST = "192.168.5.1"
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]
MOVL = "MovL(0.000000,-441.000000,947.000000,-90.000000,0.000000,180.000000)"

stop_flag = threading.Event()
rows = []


def sampler():
    try:
        s = socket.create_connection((HOST, 30005), timeout=8)
        buf = b""
        while not stop_flag.is_set():
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            while len(buf) >= 1440:
                frame, buf = buf[:1440], buf[1440:]
                rows.append((time.time(), struct.unpack_from("<6d", frame, 192)))
        s.close()
    except Exception as e:
        print("[sampler] %r" % e)


def main():
    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    time.sleep(1.0)

    s = socket.create_connection((HOST, 29999), timeout=8)
    s.settimeout(30.0)

    def cmd(name, string):
        t0 = time.time()
        s.sendall(string.encode("utf-8"))
        try:
            data = s.recv(1024)
        except socket.timeout:
            data = b"<TIMEOUT 6s>"
        print("[%-14s] -> %s" % (name, string))
        print("                 <- %r (%.2f s)" % (data.decode("utf-8", "replace"), time.time() - t0))
        return data

    cmd("GetAngle", "GetAngle()")
    cmd("GetPose", "GetPose()")
    cmd("SpeedFactor", "SpeedFactor()")
    cmd("RobotMode", "RobotMode()")

    print("\n==== 发送 MovL（同驱动格式） ====", flush=True)
    reply = cmd("MovL", MOVL)
    if reply.strip():
        cmd("Sync", "Sync()")  # 阻塞等运动完成（驱动 MoveJ 路径同款）

    t0 = time.time()
    while time.time() - t0 < 12.0:
        time.sleep(0.5)
        if rows:
            moved = max(max(r[1]) - min(r[1]) for r in [(0, [rows[0][1][i], rows[-1][1][i]]) for i in range(6)]) if len(rows) > 1 else 0
        qa = rows[-1][1] if rows else None
        print("  t=%4.1fs actual %s" % (time.time() - t0, " ".join("%+.3f" % v for v in qa) if qa else "n/a"), flush=True)
        if len(rows) > 20:
            spans = [max(r[1][i] for r in rows) - min(r[1][i] for r in rows) for i in range(6)]
            if max(spans) > 0.5:
                print("  => 已检测到运动")
                break

    # 再读一次状态（连接可能已被踢，容错）
    try:
        cmd("GetAngle2", "GetAngle()")
        cmd("RobotMode2", "RobotMode()")
    except Exception as e:
        print("[final] %r" % e)

    try:
        s.close()
    except Exception:
        pass
    stop_flag.set()
    t.join(timeout=3)

    if rows:
        print("\n==== 30005 汇总 (%d 帧) ====" % len(rows))
        for i, n in enumerate(NAMES):
            a = [r[1][i] for r in rows]
            print("%s %10.4f -> %10.4f (span %.5f)" % (n, a[0], a[-1], max(a) - min(a)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
