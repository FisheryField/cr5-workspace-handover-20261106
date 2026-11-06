# -*- coding: utf-8 -*-
"""只读诊断：控制器是否静止 + RoboDK 驱动现在是否卡死（长超时重试 ConnectedState）。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

# --- 1) 控制器 30004 ---
s = socket.create_connection((CTRL, 30004), timeout=5.0); s.settimeout(5.0)
pkt = bytearray()
while len(pkt) < 1440:
    pkt.extend(s.recv(1440 - len(pkt)))
q = struct.unpack_from('<6d', pkt, 192)
v = struct.unpack_from('<6d', pkt, 480)
mode = struct.unpack_from('<Q', pkt, 24)[0]
s.close()
print('控制器: mode=%d  速度max=%.4f°/s' % (mode, max(abs(x) for x in v)))
print('  关节@192 =', ['%.3f' % x for x in q])

# --- 2) RoboDK 驱动响应性（长超时）---
def try_api(cmd, timeout):
    try:
        c = socket.create_connection(('127.0.0.1', 20500), timeout=timeout)
        c.settimeout(timeout)
        def sl(t): c.sendall(t.encode('utf-8') + b'\n')
        def si(n): c.sendall(struct.pack('>i', n))
        def f(n):
            b = b''
            while len(b) < n:
                ch = c.recv(n - len(b))
                if not ch: raise EOFError('closed')
                b += ch
            return b
        def rl():
            b = bytearray()
            while True:
                ch = f(1)
                if ch == b'\n': return b.decode('utf-8', 'replace')
                b += ch
        sl('RDK_API'); si(3); c.sendall(struct.pack('>3d', 0.0, 0.0, 0.0))
        assert rl() == 'RDK_API'; ri = struct.unpack('>i', f(4))[0]; struct.unpack('>i', f(4))
        if struct.unpack('>i', f(4))[0] != 0:
            raise RuntimeError('handshake status != 0')
        t0 = time.time()
        sl(cmd)
        if cmd == 'ConnectedState':
            st = struct.unpack('>i', f(4))[0]; msg = rl(); status = struct.unpack('>i', f(4))[0]
            out = 'status=%d msg=%r api_status=%d' % (st, msg, status)
        elif cmd == 'Version':
            app = rl(); arch = struct.unpack('>i', f(4))[0]; ver = rl(); date = rl()
            status = struct.unpack('>i', f(4))[0]
            out = 'app=%r arch=%d ver=%r date=%r api_status=%d' % (app, arch, ver, date, status)
        else:
            out = 'unsupported'
        c.close()
        return '%.2fs  %s' % (time.time() - t0, out)
    except Exception as e:
        return '失败(%s): %s' % (time.strftime('%H:%M:%S'), e)

for cmd in ('Version', 'ConnectedState'):
    print('API %-15s → %s' % (cmd, try_api(cmd, 60)))
