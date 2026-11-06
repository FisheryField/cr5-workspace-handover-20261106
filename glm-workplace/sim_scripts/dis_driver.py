# -*- coding: utf-8 -*-
"""反汇编 RoboDK DobotCRDriver.pyc（v310，Python 3.10 嵌入式），
提取断连/重连/每条指令结束时的连接处理逻辑。只读操作，不改任何文件。"""
import dis, io, marshal, importlib.util, sys

PATH = r'D:\software\RoboDK\api\robot\v310\DobotCRDriver.pyc'
data = open(PATH, 'rb').read()
print('pyc size:', len(data))
# Python 3.10 pyc: 16 字节头（4 magic + 4 flags + 4 timestamp + 4 size）
code = marshal.loads(data[16:])
print('module code object:', code.co_name)

def walk(co, depth=0):
    yield co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            yield from walk(c, depth + 1)

funcs = {}
for co in walk(code):
    funcs[co.co_name] = co

# 关注函数：连接、断开、运动完成判定
keys = ['Connect', 'Disconnect', 'RunProgram', 'MoveJ', 'MoveL', 'Closesocket',
        'connected', 'Recv', 'Send', 'check_motion', 'wait', 'status']
print('\n=== 函数清单（按行号排序） ===')
for name, co in sorted(funcs.items(), key=lambda kv: kv[1].co_firstlineno):
    print('%5d  %s' % (co.co_firstlineno, name))

# 重点：找含有 MOVED/断连判定字符串常量的函数
print('\n=== 含断连/超时相关常量的函数 ===')
for co in walk(code):
    interesting = [c for c in co.co_consts if isinstance(c, str) and
                  any(k in c.upper() for k in ('DISCONNECT', 'NOT CONNECT', 'TIMEOUT', 'MOVED', 'FINISH'))]
    if interesting:
        print('\n--- %s (line %d) ---' % (co.co_name, co.co_firstlineno))
        for c in interesting:
            print('  const: %r' % c[:120])
