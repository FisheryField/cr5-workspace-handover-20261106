# -*- coding: utf-8 -*-
"""查 RoboDK/驱动进程 + 逐个 API 命令的响应性（找出哪些调用经驱动）。"""
import os, socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('=== 进程快照（找 RoboDK / python / dobot）===')
try:
    import subprocess
    out = subprocess.run(['wmic', 'process', 'get', 'ProcessId,Name,CommandLine', '/format:list'],
                         capture_output=True, text=True, timeout=40).stdout
    blocks = [b for b in out.split('\n\n') if b.strip()]
    for b in blocks:
        low = b.lower()
        if any(k in low for k in ('robodk', 'python', 'dobot')):
            print('  ' + ' | '.join(x.strip() for x in b.splitlines() if x.strip())
                  .replace('CommandLine=', 'CMD=')[:220])
except Exception as e:
    print('  进程枚举失败:', e)

# --- API 逐一探测 ---
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

def fresh():
    r = RDK(); r.hs(); return r

print('\n=== 逐命令响应性（每条用独立连接）===')
def probe(name, fn):
    try:
        r = fresh()
        t0 = time.time(); v = fn(r)
        print('  %-34s %.2fs  %s' % (name, time.time()-t0, v))
    except Exception as e:
        print('  %-34s 失败  %s' % (name, e))

def robot_ptr(r):
    r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
    p = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status(); return p

probe('ItemList', lambda r: (r.sl('G_List_Items'), r.si(1), r.ri(), [r.rl() for _ in range(3)], r.status())[1:3])
probe('Item("","ROBOT")', lambda r: robot_ptr(r))
probe('Robot_Pose', lambda r: (lambda p: (r.sl('G_Item_Pose'), r.s.sendall(struct.pack('>Q',p)), r.ri(),
      r.f(8*r.ri()), r.status()))(robot_ptr(r)))
probe('Robot_Joints', lambda r: (lambda p: (r.sl('G_Item_Joints'), r.s.sendall(struct.pack('>Q',p)), r.ri(),
      r.f(8*r.ri()), r.status()))(robot_ptr(r)))
probe('Robot_PoseTool', lambda r: (lambda p: (r.sl('G_Item_PoseTool'), r.s.sendall(struct.pack('>Q',p)), r.ri(),
      r.f(8*r.ri()), r.status()))(robot_ptr(r)))
probe('Robot_PoseFrame', lambda r: (lambda p: (r.sl('G_Item_PoseFrame'), r.s.sendall(struct.pack('>Q',p)), r.ri(),
      r.f(8*r.ri()), r.status()))(robot_ptr(r)))
probe('Robot_ConnectedState', lambda r: (lambda p: (r.sl('ConnectedState'), r.s.sendall(struct.pack('>Q',p)),
      r.ri(), r.rl(), r.status()))(robot_ptr(r)))
