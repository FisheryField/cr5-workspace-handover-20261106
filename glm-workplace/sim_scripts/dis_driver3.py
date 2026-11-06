# -*- coding: utf-8 -*-
"""反汇编关键函数：SendJointMovJCommands / UpdateStatus / connect / disconnect / SendCommand。
找每条指令结束后断连的发出点。"""
import dis, marshal, io, sys

PATH = r'D:\software\RoboDK\api\robot\v310\DobotCRDriver.pyc'
code = marshal.loads(open(PATH, 'rb').read()[16:])

def walk(co):
    yield co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            yield from walk(c)

funcs = {}
for co in walk(code):
    funcs.setdefault(co.co_name, []).append(co)

buf = io.StringIO()
for n in ('SendJointMovJCommands', 'UpdateStatus', 'connect', 'disconnect', 'SendCommand'):
    for co in funcs.get(n, []):
        buf.write('\n================ %s (line %d) ================' % (co.co_name, co.co_firstlineno))
        dis.dis(co, file=buf, depth=0)

open(r'D:\mydata\glm-workplace\sim_scripts\driver_dis_key.txt', 'w', encoding='utf-8').write(buf.getvalue())
print('written', len(buf.getvalue()))
# 顺带把 pyc 里的字符串常量全部倒出来（找端口/超时线索）
consts = set()
def grab(co):
    for c in co.co_consts:
        if isinstance(c, str) and 2 < len(c) < 90:
            consts.add(c)
        elif hasattr(c, 'co_name'):
            grab(c)
grab(code)
interesting = sorted(c for c in consts if any(k in c for k in
    ('29999', '30003', '30004', '22000', 'port', 'PORT', 'timeout', 'TIMEOUT',
     'connect', 'Connect', 'close', 'Close', 'recv', 'MOVED', 'Sync', 'queue')))
print('\n'.join(interesting))
