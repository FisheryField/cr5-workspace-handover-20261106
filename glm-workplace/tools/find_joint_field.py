# -*- coding: utf-8 -*-
"""只读探针：在30004报文里定位【真实关节角】字段。

背景：偏移432的字段实测为"连接时位置+指令累加"（假关节角），
v9运行后读出68.42=60.09(物理,示教器证实)+8.33(运动前位置)。
机械臂现停在v9第1瓣目标处静止，物理关节角应为：
  [60.09, 8.86, 28.20, 13.25, -19.47, -22.21]
扫描整个1440字节报文中所有连续6个double的窗口，找匹配者。
零指令，只读。"""
import io
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace', line_buffering=True)

HOST = '192.168.5.1'
PORT = 30004
EXPECTED = [60.09, 8.86, 28.20, 13.25, -19.47, -22.21]  # 第1瓣目标（示教器J1≈60.1证实）
TOL = 0.3


def read_packet(conn, deadline):
    packet = bytearray()
    while len(packet) < 1440:
        remaining = deadline - io.time_monotonic() if False else None
        part = conn.recv(1440 - len(packet))
        if not part:
            raise RuntimeError('connection closed')
        packet.extend(part)
    return packet


import time

with socket.create_connection((HOST, PORT), timeout=3.0) as conn:
    # 读2帧，取第2帧（与 _controller_feedback 相同习惯）
    for _ in range(2):
        packet = bytearray()
        while len(packet) < 1440:
            part = conn.recv(1440 - len(packet))
            if not part:
                raise RuntimeError('connection closed')
            packet.extend(part)
    time.sleep(0.05)
    # 再读一帧确认稳定
    packet2 = bytearray()
    while len(packet2) < 1440:
        part = conn.recv(1440 - len(packet2))
        if not part:
            raise RuntimeError('connection closed')
        packet2.extend(part)

length = struct.unpack_from('<Q', packet, 0)[0]
marker = struct.unpack_from('<Q', packet, 48)[0]
stamp = struct.unpack_from('<Q', packet, 32)[0]
print('帧头: length=%s marker=%s stamp=%s' % (length, hex(marker) if marker else 0, stamp))
q432 = list(struct.unpack_from('<6d', packet, 432))
print('旧字段@432（应为被污染的累加值68.42...）:', ['%.3f' % v for v in q432])

hits = []
for off in range(0, 1440 - 48, 8):
    vals = struct.unpack_from('<6d', packet, off)
    if all(abs(a - b) <= TOL for a, b in zip(vals, EXPECTED)):
        stable = struct.unpack_from('<6d', packet2, off)
        same = all(abs(a - b) < 1e-9 for a, b in zip(vals, stable))
        hits.append((off, vals, same))
        print('★ 命中 偏移%d: %s  两帧一致=%s' % (off, ['%.3f' % v for v in vals], same))

if not hits:
    print('未找到匹配窗口；打印全部可疑的6连double（与期望J1=60.09差<1°开头的）：')
    for off in range(0, 1440 - 48, 8):
        v0 = struct.unpack_from('<d', packet, off)[0]
        if abs(v0 - EXPECTED[0]) <= 1.0:
            vals = struct.unpack_from('<6d', packet, off)
            print('  偏移%d: %s' % (off, ['%.3f' % v for v in vals]))

# 顺带dump速度噪声最小的几组，供参考
print('--- 参考dump：每64字节一个double窗口（前3值） ---')
for off in range(0, 1440 - 24, 64):
    vals = struct.unpack_from('<3d', packet, off)
    print('  @%-4d %s' % (off, ['%.2f' % v for v in vals]))
