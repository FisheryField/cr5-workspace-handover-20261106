#!/usr/bin/env python3
"""Sample the CR5 30005 feedback stream at MULTIPLE candidate offsets.

Layout knowledge:
  - servo_zero_fix.py check (authoritative, validated 19:03 today) reads joint i
    at double index 24+i => byte offset 192+8i  (matches RoboDK GUI readings)
  - read_joints.py historically used 32 and 128 (proven misaligned today)

Usage: python tools/joints_sampler.py SECONDS [OUT.csv]
"""
import socket
import struct
import sys
import time

HOST, PORT = "192.168.5.1", 30005
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]
BLOCKS = [("b32", 32), ("b128", 128), ("b192", 192), ("b224", 224)]


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
    out = sys.argv[2] if len(sys.argv) > 2 else None
    s = socket.create_connection((HOST, PORT), timeout=8)
    buf = b""
    rows = []
    t0 = time.time()
    while time.time() - t0 < dur:
        chunk = s.recv(65536)
        if not chunk:
            print("!! stream closed by peer")
            break
        buf += chunk
        while len(buf) >= 1440:
            frame, buf = buf[:1440], buf[1440:]
            vals = {name: struct.unpack_from("<6d", frame, off) for name, off in BLOCKS}
            rows.append((time.time() - t0, vals))
    s.close()
    if not rows:
        print("!! no complete frame captured")
        return 2
    print("frames: %d over %.1f s" % (len(rows), rows[-1][0]))
    last = rows[-1][1]
    for bname, _ in BLOCKS:
        print("-- %s last frame: %s" % (bname, " ".join("%s=%+.4f" % (n, v) for n, v in zip(NAMES, last[bname]))))
        for i, n in enumerate(NAMES):
            a = [r[1][bname][i] for r in rows]
            print("   %s first %10.4f last %10.4f min %10.4f max %10.4f span %9.5f"
                  % (n, a[0], a[-1], min(a), max(a), max(a) - min(a)))
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write("t," + ",".join("%s_%s" % (b, n) for b, _ in BLOCKS for n in NAMES) + "\n")
            for t, vals in rows:
                f.write("%.3f," % t + ",".join("%.6f" % v for b, _ in BLOCKS for v in vals[b]) + "\n")
        print("csv -> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
