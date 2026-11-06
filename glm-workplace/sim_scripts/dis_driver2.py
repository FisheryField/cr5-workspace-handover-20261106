# -*- coding: utf-8 -*-
"""重点反汇编：UpdateStatus（断连判定）与 RunCommand（指令分发，找 Closesocket）。"""
import dis, marshal, sys

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

def dump(name, out=None):
    for co in funcs.get(name, []):
        print('\n================ %s (line %d) ================' % (co.co_name, co.co_firstlineno))
        dis.dis(co, depth=0, file=out or sys.stdout)

import io as _io
buf = _io.StringIO()
for n in ('UpdateStatus', 'RunCommand'):
    dump(n, buf)
out = buf.getvalue()
print(out[:14000])
