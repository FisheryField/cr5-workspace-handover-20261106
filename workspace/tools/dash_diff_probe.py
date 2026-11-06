#!/usr/bin/env python3
"""鉴别实验：为什么 MovL(0,-441,947,-90,0,180) 被接受却不执行。
A) MovJ 同一目标（关节空间点到点，同一坐标系解释）
B) MovL 从控制器自认位姿出发的小位移（10mm，验证直线管道是否活着）
每次都 Sync() + 30005 采样判定物理运动。
"""
import socket
import struct
import sys
import threading
import time

HOST = "192.168.5.1"
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]

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


def wait_move(timeout):
    t0 = time.time()
    moved = False
    while time.time() - t0 < timeout:
        time.sleep(0.5)
        if len(rows) > 10:
            spans = [max(r[1][i] for r in rows) - min(r[1][i] for r in rows) for i in range(6)]
            if max(spans) > 0.3:
                moved = True
                # 等到运动结束
                prev = rows[-1][1]
                for _ in range(80):
                    time.sleep(0.5)
                    cur = rows[-1][1]
                    if max(abs(cur[i] - prev[i]) for i in range(6)) < 1e-4:
                        break
                    prev = cur
                break
    return moved


def main():
    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    time.sleep(1.0)

    s = socket.create_connection((HOST, 29999), timeout=8)
    s.settimeout(60.0)

    def cmd(name, string, settle=0.2):
        t0 = time.time()
        try:
            s.sendall(string.encode("utf-8"))
            data = s.recv(2048)
        except Exception as e:
            data = ("<ERR %r>" % e).encode()
        print("[%-12s] %s\n              <- %s (%.2f s)" %
              (name, string, data.decode("utf-8", "replace").strip().replace("\n", " "), time.time() - t0), flush=True)
        time.sleep(settle)
        return data.decode("utf-8", "replace")

    n0 = len(rows)
    q = rows[-1][1] if rows else [0] * 6
    print("start actual: %s" % " ".join("%+.3f" % v for v in q))

    # ---- A: MovJ 同一目标 ----
    print("\n==== A) MovJ 同一目标 ====", flush=True)
    cmd("MovJ", "MovJ(0.000000,-441.000000,947.000000,-90.000000,0.000000,180.000000)")
    moved = wait_move(15)
    print("A result: physical moved = %s" % moved, flush=True)
    if rows:
        print("  now actual: %s" % " ".join("%+.3f" % v for v in rows[-1][1]))
    cmd("Sync", "Sync()")

    # ---- B: MovL 小位移（控制器自认位姿 +10mm Y）----
    print("\n==== B) MovL 小位移 (自认位姿 Y+10mm) ====", flush=True)
    pose = cmd("GetPose", "GetPose()")
    try:
        vals = [float(v) for v in pose.split("{")[1].split("}")[0].split(",")]
    except Exception:
        vals = None
        print("  !! GetPose 解析失败")
    if vals:
        x, y, z = vals[0], vals[1] + 10.0, vals[2]
        r = vals[3:]
        rows.clear()
        cmd("MovL10mm", "MovL({:f},{:f},{:f},{:f},{:f},{:f})".format(x, y, z, *r))
        moved = wait_move(15)
        print("B result: physical moved = %s" % moved, flush=True)
        if rows:
            print("  now actual: %s" % " ".join("%+.3f" % v for v in rows[-1][1]))
        cmd("Sync", "Sync()")
        if moved:
            # 移回去
            cmd("MovL back", "MovL({:f},{:f},{:f},{:f},{:f},{:f})".format(vals[0], vals[1], vals[2], *r))
            wait_move(15)

    cmd("GetPose end", "GetPose()")
    cmd("GetAngle end", "GetAngle()")

    stop_flag.set()
    t.join(timeout=3)
    s.close()
    if rows:
        print("\n==== 30005 汇总 (%d 帧) ====" % len(rows))
        for i, n in enumerate(NAMES):
            a = [r[1][i] for r in rows]
            print("%s %10.4f -> %10.4f" % (n, a[0], a[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
