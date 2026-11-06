# -*- coding: utf-8 -*-
"""倒出 DobotCRDriver.pyc 的 RunCommand / line_2_values / SendJointMovJCommands /
SendGetAngleCommands 完整字节码 + 字符串常量 + 名字引用（只读）。"""
import dis, io, marshal, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\software\RoboDK\api\robot\v310\DobotCRDriver.pyc'
code = marshal.loads(open(PATH, 'rb').read()[16:])

def walk(co):
    yield co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            yield from walk(c)

funcs = {co.co_name: co for co in walk(code)}
for name in ('RunCommand', 'line_2_values', 'SendJointMovJCommands',
             'SendGetAngleCommands', 'Angles2Real', 'SendSpeedCommands'):
    co = funcs.get(name)
    if co is None:
        print('!!! 未找到', name)
        continue
    print('=' * 30, name, 'line', co.co_firstlineno, '=' * 30)
    print('names:', co.co_names)
    print('varnames:', co.co_varnames)
    consts_str = [c for c in co.co_consts if isinstance(c, (str, int, float)) and c is not None]
    print('consts:', consts_str[:80])
    print('--- dis ---')
    dis.dis(co)
    print()
