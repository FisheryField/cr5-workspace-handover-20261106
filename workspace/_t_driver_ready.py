# -*- coding: utf-8 -*-
"""安全测试：驱动在"假报断连/重连"后是否还接受运动指令。
   用零位移 MoveJ（目标 = 当前关节），即使被接受也不产生任何实际运动。"""
import socket, struct, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class RDK:
    def __init__(self, host='127.0.0.1', port=20500, timeout=20):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
    def sl(self, t): self.s.sendall(t.replace('\n', '<br>').encode('utf-8') + b'\n')
    def si(self, n): self.s.sendall(struct.pack('>i', n))
    def sa(self, vals):
        self.si(len(vals)); self.s.sendall(struct.pack('>' + str(len(vals)) + 'd', *vals))
    def _f(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c: raise EOFError('closed')
            b += c
        return b
    def rl(self):
        b = bytearray()
        while True:
            c = self._f(1)
            if c == b'\n': return b.decode('utf-8', 'replace')
            b += c
    def ri(self): return struct.unpack('>i', self._f(4))[0]
    def status(self):
        st = self.ri()
        if st != 0:
            msg = self.rl() if (st in (2,3) or st < 100) else ''
            raise RuntimeError('status=%s %s' % (st, msg))
        return st
    def handshake(self):
        self.sl('RDK_API'); self.sa([0.0, 0.0, 0.0])
        r = self.rl(); v = self.ri(); b = self.ri(); self.status(); return r, v, b

r = RDK()
print('握手:', r.handshake())

def item_by_name(nm, typ=None):
    if typ is None:
        r.sl('G_Item'); r.sl(nm)
    else:
        r.sl('G_Item2'); r.sl(nm); r.si(typ)
    ptr, t = struct.unpack('>Q', r._f(8))[0], struct.unpack('>i', r._f(4))[0]
    r.status(); return ptr

def name_of(ptr):
    r.sl('G_Name'); r.s.sendall(struct.pack('>Q', ptr)); v = r.rl(); r.status(); return v

robot = item_by_name('', 2)
print('机器人 item:', robot, name_of(robot))

# 运行模式
r.sl('G_RunMode'); runmode = r.ri(); r.status()
print('RunMode =', runmode)
r.sl('S_RunMode'); r.si(1); r.status()   # RUNMODE_RUN_ROBOT
print('已设为 RUNMODE_RUN_ROBOT')

def connected_state():
    r.sl('ConnectedState'); st = r.ri(); msg = r.rl(); r.status(); return st, msg

print('ConnectedState =', connected_state())

# 当前关节
r.sl('G_Item_Joints'); r.s.sendall(struct.pack('>Q', robot))
n = r.ri(); q = list(struct.unpack('>' + str(n) + 'd', r._f(8*n))); r.status()
print('当前关节 =', ['%.4f' % v for v in q[:6]])

# 零位移 MoveJ：目标 = 当前关节
print('\n>>> 发送零位移 MoveJ（目标=当前关节，不会产生实际运动）…')
t0 = time.time()
tgt = list(q[:6])
r.sl('MoveJ_Blocking' if False else 'MoveJ'); r.s.sendall(struct.pack('>Q', robot))
r.si(6); r.s.sendall(struct.pack('>6d', *tgt))
try:
    r.status()
    print('    [OK] 驱动接受了 MoveJ，用时 %.2fs（说明重连后指令可用）' % (time.time()-t0))
except Exception as e:
    print('    [FAIL] 驱动拒绝/出错：%.2fs  %s' % (time.time()-t0, e))

time.sleep(0.5)
print('之后 ConnectedState =', connected_state())
r.sl('G_Item_Joints'); r.s.sendall(struct.pack('>Q', robot))
n = r.ri(); q2 = list(struct.unpack('>' + str(n) + 'd', r._f(8*n))); r.status()
print('之后关节 =', ['%.4f' % v for v in q2[:6]])
