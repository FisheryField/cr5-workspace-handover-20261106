# -*- coding: utf-8 -*-
# 只读：站内宏导出 → 与磁盘母本比 MD5（三连之三）
import sys, io, os, hashlib, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

DISK = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
NAME = 'TCP真实运动_P2P版'
RDK = Robolink()

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest().upper()

items = [it for it in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == NAME]
if len(items) != 1:
    raise SystemExit('station macro count = %d (!=1)' % len(items))
tmp = os.path.join(tempfile.mkdtemp(dir=r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump'), 'md5_check.py')
items[0].Save(tmp)

a, b = md5(tmp), md5(DISK)
sa, sb = os.path.getsize(tmp), os.path.getsize(DISK)
print('station:', a, sa, 'B')
print('disk   :', b, sb, 'B')
print('MATCH =', a == b)
