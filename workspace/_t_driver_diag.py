# -*- coding: utf-8 -*-
"""查 RoboDK Dobot 驱动的编译版本目录 / Python 版本设置 / 驱动日志，并问机器人连接参数。"""
import glob, os, socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = r'D:\software\RoboDK\api\Robot'
print('=== api\\Robot 下与 Dobot 相关 ===')
for p in sorted(glob.glob(os.path.join(base, '**', '*Dobot*'), recursive=True)):
    print('  %s  (%s B)' % (p, os.path.getsize(p) if os.path.isfile(p) else 'dir'))
print('\n=== 版本目录 vXX ===')
for p in sorted(glob.glob(os.path.join(base, 'v*'))):
    print('  ', p)

print('\n=== settings.ini 里的 Python / Driver 设置 ===')
ini = r'C:\Users\FisheryField\AppData\Roaming\RoboDK\settings.ini'
for line in open(ini, encoding='utf-8', errors='replace'):
    l = line.strip()
    if any(k in l.lower() for k in ('python', 'driver', 'dobot', 'robot', 'path')):
        print('  ', l)

print('\n=== 最近修改的日志类文件（RoboDK 相关，3 天内）===')
roots = [r'D:\software\RoboDK\bin', r'D:\software\RoboDK\api', r'C:\Users\FisheryField\Documents\RoboDK',
         r'C:\Users\FisheryField\AppData\Roaming\RoboDK']
now = time.time()
for root in roots:
    for dirpath, dirs, files in os.walk(root):
        if '.vscodium2' in dirpath:
            continue
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                mt = os.path.getmtime(fp)
            except OSError:
                continue
            if now - mt < 3 * 86400 and (f.lower().endswith(('.log', '.txt')) or 'log' in f.lower()):
                print('  %s  %8d  %s' % (time.strftime('%m-%d %H:%M', time.localtime(mt)), os.path.getsize(fp), fp))

# --- API 询问连接参数 ---
class RDK:
    def __init__(self, t=10):
        self.s = socket.create_connection(('127.0.0.1', 20500), timeout=t); self.s.settimeout(t)
    def sl(self, x): self.s.sendall(x.replace('\n', '<br>').encode('utf-8') + b'\n')
    def si(self, n): self.s.sendall(struct.pack('>i', n))
    def f(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c: raise EOFError
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
        self.sl('RDK_API'); self.si(3); self.s.sendall(struct.pack('>3d',0.,0.,0.))
        assert self.rl() == 'RDK_API'; self.ri(); self.ri(); self.status()

r = RDK(); r.hs()
r.sl('G_Item2'); r.sl('Dobot CR5'); r.si(2)
ROBOT = struct.unpack('>Q', r.f(8))[0]; struct.unpack('>i', r.f(4)); r.status()
print('\n=== 机器人连接参数 ===')
for cmd in ('G_Item_ConnectionParams', 'G_Item_ConnectedState'):
    try:
        t0 = time.time()
        r.sl(cmd); r.s.sendall(struct.pack('>Q', ROBOT))
        if cmd.endswith('ConnectionParams'):
            n = r.ri()
            vals = list(struct.unpack('>' + str(n) + 'd', r.f(8*n))) if n > 0 else []
            # 字符串形式
            s = r.rl()
            print('  %s → %.2fs n=%d vals=%s str=%r' % (cmd, time.time()-t0, n, vals, s))
        else:
            st = r.ri(); msg = r.rl()
            print('  %s → %.2fs status=%s msg=%r' % (cmd, time.time()-t0, st, msg))
        r.status()
    except Exception as e:
        print('  %s → 失败: %s' % (cmd, e))
