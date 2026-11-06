# -*- coding: utf-8 -*-
# v14a：替换站内 P2P 宏为磁盘最新版（删除旧条目 + AddFile 新源）。
# 不改 v12b、不保存工作站。
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

SRC = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
NAME = 'TCP真实运动_P2P版'
RDK = Robolink()

items = [it for it in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == NAME]
for it in items:
    it.Delete()
    print('deleted old:', NAME, 'x%d' % len(items))
item = RDK.AddFile(SRC)
print('added:', item.Name(), 'valid:', item.Valid())

# 回读验证版本号
import tempfile, os, re
d = tempfile.mkdtemp(dir=r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump')
out = os.path.join(d, 'verify_v14a.py')
for it in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON):
    if it.Name() == NAME:
        it.Save(out)
        src = open(out, encoding='utf-8', errors='replace').read()
        m = re.search(r"LOG_VERSION = '([^']+)'", src)
        print('station macro LOG_VERSION =', m.group(1) if m else 'NOT FOUND')
        break
