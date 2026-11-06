# -*- coding: utf-8 -*-
"""实验：RoboDK driver 的 MoveJ 指令是否真的送到了控制器。
   发 J1 = 当前 +1° 的 MoveJ（观察级小动作），再用 30003 GetAngle() 独立核对。"""
import re, socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

def native(cmd, port=30003, wait=3.0):
    s = socket.create_connection((CTRL, port), timeout=6.0); s.settimeout(wait)
    try:
        s.sendall((cmd + '\n').encode())
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
        return b.decode('utf-8', 'replace').strip()
    finally:
        s.close()

def cur():
    t = native('GetAngle()')
    return [float(x) for x in re.findall(r'-?\d+\.\d+', t)[:6]], t

q0, raw0 = cur()
print('起点 :', q0)
print('      ', raw0)

target = q0[:]
target[0] += 1.0
print('目标 :', ['%.3f' % v for v in target], ' (仅 J1 +1°)')

class RDK:
    def __init__(self, t=60):
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

r = RDK(60); r.hs()
r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
p = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()

print('\n>>> 发送 MoveJ（J1 +1°）…', flush=True)
t0 = time.time()
try:
    r.sl('MoveJ'); r.s.sendall(struct.pack('>Q', p))
    r.si(6); r.s.sendall(struct.pack('>6d', *target))
    r.status()
    print('    [driver 返回正常] %.1fs' % (time.time() - t0))
except Exception as e:
    print('    [driver 报错/超时] %.1fs  %s' % (time.time() - t0, e))

for k in (1, 2, 4, 7, 10):
    time.sleep(k if k == 1 else 1.0)
    q, raw = cur()
    d = [round(a - b, 4) for a, b in zip(q, q0)]
    print('  t=%-4.1fs 真机 = %s   ΔJ1=%+.4f  %s' % (
        time.time() - t0, ['%.4f' % v for v in q], d[0],
        '← 指令已被执行！' if abs(d[0]) > 0.05 else ''))
