# -*- coding: utf-8 -*-
"""通过 RoboDK API (TCP 20500) 询问当前工作站的条目树与脚本条目。"""
import socket, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class RDK:
    def __init__(self, host='127.0.0.1', port=20500, timeout=10):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b''
    def cmd(self, c):
        self.s.sendall(c.encode('utf-8') + b'\x00')
        # 读到 \x00 结束
        while b'\x00' not in self.buf:
            chunk = self.s.recv(65536)
            if not chunk:
                break
            self.buf += chunk
        line, _, rest = self.buf.partition(b'\x00')
        self.buf = rest
        return line.decode('utf-8', 'replace')

r = RDK()
print('API 版本:', r.cmd('Version'))
print('RoboDK 版本:', r.cmd('RoboDK Version'))
names = r.cmd('ItemList').split(',')
print('\n站内条目数 =', len(names))
print('--- 全部条目 ---')
for i, n in enumerate(names):
    print('  %2d  %r' % (i, n))

print('\n--- 逐个查类型/父级 ---')
for n in names:
    try:
        # ITEM_TYPE_*: 32 = ? ; 用 ItemType 命令
        t = r.cmd('ItemType\t%s' % n)
        print('  %-40r type=%s' % (n, t))
        if t.strip() in ('10', '20', '31'):  # 程序/脚本类
            print('      父级:', r.cmd('Parent\t%s' % n))
            print('      文件名:', r.cmd('Filename\t%s' % n))
    except Exception as e:
        print('  %r 出错 %s' % (n, e))
