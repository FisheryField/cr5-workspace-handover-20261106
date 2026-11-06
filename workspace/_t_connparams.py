# -*- coding: utf-8 -*-
"""① 读机器人连接参数（轻量）② 只读验证控制器 30003 命令口（不发任何运动）。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

class RDK:
    def __init__(self, t=8):
        self.s = socket.create_connection(('127.0.0.1', 20500), timeout=t); self.s.settimeout(t)
    def sl(self, x): self.s.sendall(x.replace('\n', '<br>').encode('utf-8') + b'\n')
    def si(self, n): self.s.sendall(struct.pack('>i', n))
    def f(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c: raise EOFError('closed')
            b += c
        return b
    def rl(self):
        b = bytearray()
        while True:
            c = self.f(1)
            if c == b'\n': return b.decode('utf-8', 'replace')
            b += c
    def ri(self): return struct.unpack('>i', self.f(4))[0]
    def status(self):
        st = self.ri()
        if st != 0: raise RuntimeError('status=%s %s' % (st, self.rl()))
    def hs(self):
        self.sl('RDK_API'); self.si(3); self.s.sendall(struct.pack('>3d', 0., 0., 0.))
        assert self.rl() == 'RDK_API'; self.ri(); self.ri(); self.status()

r = RDK(); r.hs()
r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
p = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()

print('=== 尝试读取连接参数 ===')
for cmd in ('ConnectionParams', 'G_Item_ConnectionParams', 'Robot_ConnectionParams'):
    try:
        t0 = time.time()
        r.sl(cmd); r.s.sendall(struct.pack('>Q', p))
        n = r.ri()
        nums = list(struct.unpack('>' + str(n) + 'd', r.f(8*n))) if n > 0 else []
        st = r.rl() if cmd.startswith('G_Item') else None
        print('  %-28s %.2fs n=%d nums=%s  str=%r' % (cmd, time.time()-t0, n, nums, st))
        r.status()
    except Exception as e:
        print('  %-28s 失败: %s' % (cmd, e))

# ---- 30003 命令口（只读命令）----
print('\n=== 控制器 30003 命令口（只读命令）===')
try:
    s = socket.create_connection((CTRL, 30003), timeout=6.0); s.settimeout(6.0)
    buf = b''
    t0 = time.time()
    while b'{}' not in buf and len(buf) < 4096 and time.time() - t0 < 6:
        c = s.recv(4096)
        if not c: break
        buf += c
    print('  欢迎/首包: %r' % buf[:200])
    for cmd in ('RobotMode()', 'GetAngle()', 'GetPose()', 'GetErrorID()', 'SpeedFactor()'):
        s.sendall((cmd + '\n').encode())
        b = b''
        t1 = time.time()
        while time.time() - t1 < 6:
            try:
                c = s.recv(4096)
            except socket.timeout:
                break
            if not c: break
            b += c
            if b.count(b'{') >= 1 and b.rstrip().endswith(b'}'):
                break
        print('  %-14s → %r' % (cmd, b.decode('utf-8', 'replace').strip()[:160]))
    s.close()
except Exception as e:
    print('  30003 失败:', e)
