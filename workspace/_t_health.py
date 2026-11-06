# -*- coding: utf-8 -*-
"""解卡后体检（全只读）：驱动响应 / 当前工作站 / 模型关节 vs 真机 30004 @192。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

# ---- 真机 ----
s = socket.create_connection((CTRL, 30004), timeout=5.0); s.settimeout(5.0)
pkt = bytearray()
while len(pkt) < 1440:
    pkt.extend(s.recv(1440 - len(pkt)))
real = struct.unpack_from('<6d', pkt, 192)
mode = struct.unpack_from('<Q', pkt, 24)[0]
vel = struct.unpack_from('<6d', pkt, 480)
s.close()
print('真机 30004 @192 = %s  mode=%d  vmax=%.4f' %
      (['%.4f' % v for v in real], mode, max(abs(x) for x in vel)))

# ---- RoboDK API ----
class RDK:
    def __init__(self, t=15):
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
        self.sl('RDK_API'); self.si(3); self.s.sendall(struct.pack('>3d', 0., 0., 0.))
        assert self.rl() == 'RDK_API'; self.ri(); self.ri(); self.status()

def timed(label, fn):
    t0 = time.time()
    try:
        v = fn()
        print('%-30s → %.2fs  %s' % (label, time.time()-t0, v))
        return v
    except Exception as e:
        print('%-30s → %.2fs  失败: %s' % (label, time.time()-t0, e))
        return None

r = RDK(); r.hs()
timed('Version', lambda: (r.sl('Version'), r.rl(), r.ri(), r.rl(), r.rl(), r.status())[1])

# 当前工作站名
def stn():
    r.sl('G_Item2'); r.sl(''); r.si(1)
    p = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()
    r.sl('G_Name'); r.s.sendall(struct.pack('>Q', p)); nm = r.rl(); r.status(); return nm
timed('当前工作站', stn)

# 机器人
r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
ROBOT = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()
timed('ConnectedState', lambda: (r.sl('ConnectedState'), r.ri(), r.rl(), r.status())[1:3])
timed('RunMode', lambda: (r.sl('G_RunMode'), r.ri(), r.status())[1])

def jc(cmd):
    r.sl(cmd); r.s.sendall(struct.pack('>Q', ROBOT))
    n = r.ri()
    if n <= 0:
        r.status(); return 'empty'
    v = list(struct.unpack('>' + str(n) + 'd', r.f(8*n))); r.status()
    return ['%.4f' % x for x in v[:6]]

mj = timed('模型关节 SimulatorJoints', lambda: jc('G_Item_SimulatorJoints'))
timed('模型关节 Joints', lambda: jc('G_Item_Joints'))

if isinstance(mj, list):
    dev = max(abs(float(a)-b) for a, b in zip(mj, real))
    print('\n模型 vs 真机 最大偏差 = %.4f°  → %s' % (dev, '✔ 模型可当判据用' if dev < 0.5 else '✘ 模型与真机不符（不能直接用）'))
