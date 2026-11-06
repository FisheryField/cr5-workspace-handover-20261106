# -*- coding: utf-8 -*-
"""反汇编 v39 DobotCRDriver.pyc 的 RunCommand，找 MOVL 分支的调用方法。"""
import marshal, dis, io, sys

data = open(r'D:\software\RoboDK\api\robot\v39\DobotCRDriver.pyc','rb').read()
code = marshal.loads(data[16:])

def find(c, name):
    for k in c.co_consts:
        if hasattr(k, 'co_name'):
            if k.co_name == name:
                return k
            r = find(k, name)
            if r:
                return r
    return None

f = find(code, 'RunCommand')
buf = io.StringIO()
dis.dis(f, file=buf)
txt = buf.getvalue().splitlines()

needle = sys.argv[1] if len(sys.argv) > 1 else 'MOVL'
exclude = sys.argv[2] if len(sys.argv) > 2 else 'MOVLSEARCH'
hits = [i for i, line in enumerate(txt) if ("'" + needle + "'") in line and exclude not in line]
for i in hits[:1]:
    print('\n'.join(l.rstrip()[:160] for l in txt[max(0,i-4):i+60]))

# 顺带列出 ComRobot 类的方法名清单，确认有无 MovL 类方法
cls = find(code, 'ComRobot')
print('\n== ComRobot methods ==')
for k in cls.co_consts:
    if hasattr(k, 'co_name'):
        print(' ', k.co_name)
