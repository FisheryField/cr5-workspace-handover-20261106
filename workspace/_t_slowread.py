# -*- coding: utf-8 -*-
"""长超时只读：驱动取模型关节到底能不能成功、要多久。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class RDK:
    def __init__(self, t):
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

TIMEOUT = 90
for cmd in ('G_Item_SimulatorJoints', 'G_Item_Joints'):
    try:
        t0 = time.time()
        r = RDK(TIMEOUT); r.hs()
        r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
        p = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()
        r.sl(cmd); r.s.sendall(struct.pack('>Q', p))
        n = r.ri()
        vals = list(struct.unpack('>' + str(n) + 'd', r.f(8*n))) if n > 0 else []
        r.status()
        print('%-26s %.1fs  n=%d  %s' % (cmd, time.time()-t0, n, ['%.4f' % v for v in vals[:6]]))
    except Exception as e:
        print('%-26s 失败(>%ds): %s' % (cmd, TIMEOUT, e))
