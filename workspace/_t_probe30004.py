# -*- coding: utf-8 -*-
"""只读探测：30004 反馈帧里 offset 192 / 432 / 480 的含义对比 dashboard GetAngle()。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

def dashboard(cmds, port=29999, timeout=4.0):
    out = []
    try:
        s = socket.create_connection((CTRL, port), timeout=timeout)
        s.settimeout(timeout)
        f = s.makefile('rwb', buffering=0)
        f.readline()  # 欢迎行
        for c in cmds:
            f.write((c + '\n').encode())
            out.append(f.readline().decode('utf-8', 'replace').strip())
        s.close()
    except Exception as e:
        out.append('ERR %s' % e)
    return out

print('=== dashboard(29999) 只读 ===')
for line in dashboard(['RobotMode()', 'GetAngle()', 'GetErrorID()']):
    print('  ', line)

print('\n=== 30004 反馈帧（只读，取 3 帧）===')
s = socket.create_connection((CTRL, 30004), timeout=5.0)
s.settimeout(5.0)
prev = None
for i in range(3):
    pkt = bytearray()
    while len(pkt) < 1440:
        part = s.recv(1440 - len(pkt))
        if not part:
            break
        pkt.extend(part)
    if len(pkt) != 1440:
        print('  帧长异常', len(pkt)); break
    length = struct.unpack_from('<Q', pkt, 0)[0]
    mode   = struct.unpack_from('<Q', pkt, 24)[0]
    stamp  = struct.unpack_from('<Q', pkt, 32)[0]
    marker = struct.unpack_from('<Q', pkt, 48)[0]
    q192 = struct.unpack_from('<6d', pkt, 192)
    q432 = struct.unpack_from('<6d', pkt, 432)
    v480 = struct.unpack_from('<6d', pkt, 480)
    print('\n  帧%d: len=%d marker=%x mode=%d stamp=%d' % (i, length, marker, mode, stamp))
    print('   @192 =', ['%9.4f' % v for v in q192])
    print('   @432 =', ['%9.4f' % v for v in q432])
    print('   @480(速度) =', ['%8.4f' % v for v in v480])
    if prev is not None:
        print('   @192 帧间变化 =', ['%.6f' % (a-b) for a, b in zip(q192, prev)])
    prev = q192
s.close()
