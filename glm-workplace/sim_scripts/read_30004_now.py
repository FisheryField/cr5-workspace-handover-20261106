# -*- coding: utf-8 -*-
"""只读：直连控制器 30004 取真实关节/速度/模式（绕开 RoboDK 与 GUI 争抢）。"""
import sys, io, socket, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '192.168.5.1'
with socket.create_connection((HOST, 30004), timeout=3.0) as conn:
    packet = bytearray()
    while len(packet) < 1440:
        part = conn.recv(1440 - len(packet))
        if not part:
            raise SystemExit('连接被关闭')
        packet.extend(part)

length = struct.unpack_from('<Q', packet, 0)[0]
marker = struct.unpack_from('<Q', packet, 48)[0]
mode = struct.unpack_from('<Q', packet, 24)[0]
q = list(struct.unpack_from('<6d', packet, 192))
vel = list(struct.unpack_from('<6d', packet, 480))
assert length == 1440 and marker == 0x123456789ABCDEF, '帧格式不匹配'
print('模式 = %d （5=使能）' % mode)
print('真实关节 = [%s]' % ', '.join('%.3f' % v for v in q))
print('速度     = [%s]  max|v|=%.3f' % (', '.join('%.3f' % v for v in vel), max(abs(v) for v in vel)))
print('判读:', '已在零位' if all(abs(v) < 0.05 for v in q) else ('静止（不在零位）' if max(abs(v) for v in vel) < 1.0 else '运动中'))
