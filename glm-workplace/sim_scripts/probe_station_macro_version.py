# -*- coding: utf-8 -*-
# 只读探针：查询活动站内 P2P 宏的版本与站内条目概况（不删除、不添加、不保存）。
import sys, io, tempfile, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

NAME = 'TCP真实运动_P2P版'
RDK = Robolink()
station = RDK.ActiveStation()
print('active station:', station.Name())

items = [it for it in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == NAME]
if not items:
    print('station macro: NOT FOUND (need refresh)')
else:
    for it in items:
        d = tempfile.mkdtemp(dir=r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump')
        out = os.path.join(d, 'probe_read.py')
        it.Save(out)
        src = open(out, encoding='utf-8', errors='replace').read()
        m = re.search(r"LOG_VERSION = '([^']+)'", src)
        print('station macro LOG_VERSION =', m.group(1) if m else 'NOT FOUND', '| bytes =', len(src.encode("utf-8", "replace")))

obs = [o.Name() for o in RDK.ItemList() if o.Type() in (3,)]  # ITEM_TYPE_OBJECT=3
print('objects:', obs)
