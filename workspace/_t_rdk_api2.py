# -*- coding: utf-8 -*-
"""最小 RoboDK API 客户端（协议照抄 robolink.py），用于查询当前工作站条目树。"""
import socket, struct, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class RDK:
    def __init__(self, host='127.0.0.1', port=20500, timeout=15):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)

    def send_line(self, t):
        self.s.sendall(t.replace('\n', '<br>').encode('utf-8') + b'\n')

    def send_int(self, n):
        self.s.sendall(struct.pack('>i', n))

    def send_array(self, vals):
        self.send_int(len(vals))
        self.s.sendall(struct.pack('>' + str(len(vals)) + 'd', *vals))

    def _fill(self, n):
        buf = b''
        while len(buf) < n:
            c = self.s.recv(n - len(buf))
            if not c:
                raise EOFError('连接关闭')
            buf += c
        return buf

    def rec_line(self):
        buf = bytearray()
        while True:
            c = self._fill(1)
            if c == b'\n':
                return buf.decode('utf-8', 'replace')
            buf += c

    def rec_int(self):
        return struct.unpack('>i', self._fill(4))[0]

    def rec_item(self):
        ptr = struct.unpack('>Q', self._fill(8))[0]
        typ = struct.unpack('>i', self._fill(4))[0]
        return ptr, typ

    def status(self):
        st = self.rec_int()
        if st != 0:
            msg = self.rec_line() if st in (2, 3) or st < 100 else ''
            raise RuntimeError('status=%s %s' % (st, msg))
        return st

    def handshake(self):
        self.send_line('RDK_API')
        self.send_array([0.0, 0.0, 0.0])
        resp = self.rec_line()
        ver_api = self.rec_int()
        build = self.rec_int()
        self.status()
        return resp, ver_api, build

r = RDK()
print('握手:', r.handshake())

r.send_line('Version'); 
app = r.rec_line(); arch = r.rec_int(); ver = r.rec_line(); date = r.rec_line(); r.status()
print('RoboDK = %s (%s, %s) %s' % (ver, app, arch, date))

# 站名
r.send_line('G_Item2'); r.send_line(''); r.send_int(1)
ptr, typ = r.rec_item(); r.status()
r.send_line('G_Name'); self_ptr = ptr
r.s.sendall(struct.pack('>Q', ptr))
name = r.rec_line(); r.status()
print('当前工作站 =', repr(name))

# 条目名列表
r.send_line('G_List_Items')
r.send_int(1)
count = r.rec_int()
print('条目数 =', count)
for i in range(count):
    nm = r.rec_line()
    print('  %2d %s' % (i, nm))
r.status()

# 按类型列（10 = PROGRAM_PYTHON, 8 = PROGRAM, 5 = OBJECT）
for label, t in (('PYTHON 脚本(10)', 10), ('程序(8)', 8), ('物体(5)', 5), ('机器人(2)', 2), ('坐标系(3)', 3), ('工具(4)', 4)):
    r.send_line('G_List_Items_Type'); r.send_int(t)
    c = r.rec_int()
    out = [r.rec_line() for _ in range(c)]
    r.status()
    print('\n%s 共 %d:' % (label, c))
    for nm in out:
        print('   ', repr(nm))
