# -*- coding: utf-8 -*-
"""只读：列出站内所有 Python 宏，找出 TCP 仿真类脚本并打印其障碍物元组行。"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

RDK = Robolink()
progs = RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)
print('站内 Python 宏：', progs if isinstance(progs, list) and progs and isinstance(progs[0], str) else [p if isinstance(p, str) else p.Name() for p in progs])
for p in progs:
    name = p if isinstance(p, str) else p.Name()
    it = p if not isinstance(p, str) else RDK.Item(p)
    try:
        code = it.setParam('Code').replace('<br>', '\n')
    except Exception as e:
        print('  [%s] 读取失败: %s' % (name, e))
        continue
    hits = re.findall(r"for name in \([^)]*\)", code)
    ver = re.findall(r"LOG_VERSION = '([^']*)'", code)
    has_baffle = '挡板' in code
    print('--- %s ｜ LOG_VERSION=%s ｜ 含"挡板"字样=%s' % (name, ver[0] if ver else '-', has_baffle))
    for h in hits:
        print('    障碍物元组:', h)
