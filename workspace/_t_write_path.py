# -*- coding: utf-8 -*-
"""决定性测试：RoboDK 驱动的【写路径】是否可用。
   发一条零位移 MoveJ（目标=真机当前关节 ⇒ 即使执行也不动），
   前后各用 30003 GetAngle() 独立核对真机位置。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

def native(cmds, port=30003, wait=3.0):
    out = []
    s = socket.create_connection((CTRL, port), timeout=6.0); s.settimeout(wait)
    try:
        for c in cmds:
            s.sendall((c + '\n').encode())
            b = b''
            t0 = time.time()
            while time.time() - t0 < wait:
                try:
                    p = s.recv(4096)
                except socket.timeout:
                    break
                if not p: break
                b += p
                if b'}' in b: break
            out.append(b.decode('utf-8', 'replace').strip())
    finally:
        s.close()
    return out

a0 = native(['GetAngle()', 'RobotMode()'])
print('起点(30003)：', a0)

class RDK:
    def __init__(self, t=20):
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

# 真机当前关节（从 30003 文本解析）
import re
nums = re.findall(r'-?\d+\.\d+', a0[0])
cur = [float(x) for x in nums[:6]]
print('解析当前关节 =', cur)

r = RDK(18); r.hs()
r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
p = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()
print('ConnectedState =', end=' ')
r.sl('ConnectedState'); r.s.sendall(struct.pack('>Q', p))
print(struct.unpack('>i', r.f(4))[0], r.rl(), end=' '); r.status(); print('ok')

print('\n>>> 发送零位移 MoveJ（目标 = 当前关节）', flush=True)
t0 = time.time()
try:
    r.sl('MoveJ'); r.s.sendall(struct.pack('>Q', p))
    r.si(6); r.s.sendall(struct.pack('>6d', *cur))
    r.status()
    print('    [写路径可用] MoveJ 返回，用时 %.2fs' % (time.time() - t0))
except Exception as e:
    print('    [写路径不可用] %.2fs  %s' % (time.time() - t0, e))

time.sleep(1.0)
a1 = native(['GetAngle()'])
print('之后(30003)：', a1)
