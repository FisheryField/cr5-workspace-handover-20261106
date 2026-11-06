# -*- coding: utf-8 -*-
"""只读实测：RoboDK 模型关节（SimulatorJoints / Joints）与真机实际关节是否一致。
   真机实际关节 = 30004 帧 @192（已实证）。不发任何运动指令。"""
import socket, struct, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

# --- 真机 ---
s = socket.create_connection((CTRL, 30004), timeout=5.0); s.settimeout(5.0)
pkt = bytearray()
while len(pkt) < 1440:
    pkt.extend(s.recv(1440 - len(pkt)))
real = struct.unpack_from('<6d', pkt, 192)
mode = struct.unpack_from('<Q', pkt, 24)[0]
s.close()
print('真机 30004 @192  =', ['%9.4f' % v for v in real], ' mode=%d' % mode)

# --- RoboDK API ---
class RDK:
    def __init__(self, t=25):
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
        if st != 0:
            m = self.rl() if (st in (2,3) or st < 100) else ''
            raise RuntimeError('status=%s %s' % (st, m))
    def hs(self):
        self.sl('RDK_API'); self.si(3); self.s.sendall(struct.pack('>3d',0.,0.,0.))
        assert self.rl() == 'RDK_API'; self.ri(); self.ri(); self.status()

def joints_cmd(cmd, r):
    r.sl(cmd); r.s.sendall(struct.pack('>Q', ROBOT))
    n = r.ri()
    if n <= 0:
        r.status(); return None
    v = list(struct.unpack('>' + str(n) + 'd', r.f(8*n)))
    r.status(); return v

r = RDK(); r.hs()
r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
ROBOT = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()

for cmd in ('G_Item_Joints', 'G_Item_SimulatorJoints', 'G_Item_Joints_Real'):
    try:
        q = joints_cmd(cmd, r)
        if q is None:
            print('%-28s → 空' % cmd); continue
        dev = max(abs(a-b) for a, b in zip(q[:6], real))
        print('%-28s → %s   与真机最大偏差=%.4f° %s'
              % (cmd, ['%9.4f' % v for v in q[:6]], dev, '✔一致' if dev < 0.5 else '✘不一致'))
    except Exception as e:
        print('%-28s → 失败 %s' % (cmd, e))
