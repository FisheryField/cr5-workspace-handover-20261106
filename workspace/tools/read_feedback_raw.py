#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用与脚本完全相同的解析读 30004 实时反馈，看 mode 与 velocity 的真实值（只读）。"""
import math
import socket
import struct
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'


def feedback(timeout=3.0):
    with socket.create_connection((HOST, 30004), timeout=timeout) as c:
        packet = bytearray()
        deadline = time.monotonic() + timeout
        while len(packet) < 1440:
            rem = deadline - time.monotonic()
            if rem <= 0:
                raise RuntimeError('timeout')
            c.settimeout(rem)
            part = c.recv(1440 - len(packet))
            if not part:
                raise RuntimeError('closed')
            packet.extend(part)
    length = struct.unpack_from('<Q', packet, 0)[0]
    mode = struct.unpack_from('<Q', packet, 24)[0]
    stamp = struct.unpack_from('<Q', packet, 32)[0]
    marker = struct.unpack_from('<Q', packet, 48)[0]
    q = list(struct.unpack_from('<6d', packet, 432))
    v = list(struct.unpack_from('<6d', packet, 480))
    return length, mode, stamp, marker, q, v


print('取样 8 次（每次间隔 1 秒）——看 mode 与 max|velocity| 是否稳定在 0 附近：')
print('  # | len | mode | marker     | max|v| (°/s) | 各轴速度 | 各轴角度')
for i in range(8):
    try:
        length, mode, stamp, marker, q, v = feedback()
        print('  %d | %4d | %4d | %#x | %11.5f | %s | %s'
              % (i, length, mode, marker, max(abs(x) for x in v),
                 ','.join('%+.3f' % x for x in v), ','.join('%+.3f' % x for x in q)))
        assert length == 1440 and marker == 0x123456789ABCDEF and all(math.isfinite(x) for x in q + v)
    except Exception as e:  # noqa: BLE001
        print('  %d | 读取失败: %s: %s' % (i, type(e).__name__, e))
    time.sleep(1)
