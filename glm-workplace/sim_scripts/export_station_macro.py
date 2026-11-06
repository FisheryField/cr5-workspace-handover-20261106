# -*- coding: utf-8 -*-
# 只读导出：把当前 RoboDK 站内的 'TCP真实运动' 宏源码导出到工作区临时目录，
# 用于离线比对版本。不修改站、不修改宏、不保存站。
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

OUT_DIR = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump'
os.makedirs(OUT_DIR, exist_ok=True)

RDK = Robolink()
items = RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)
macro = None
for it in items:
    if it.Name() == 'TCP真实运动':
        macro = it
        break
if macro is None:
    print('NOT FOUND: TCP真实运动')
    sys.exit(1)
out = os.path.join(OUT_DIR, 'TCP真实运动_station.py')
macro.Save(out)
print('exported ->', out, os.path.getsize(out), 'bytes')

# 顺带导出新增的 P2P 宏以供比对
for it in items:
    if it.Name() == 'TCP真实运动_P2P版':
        out2 = os.path.join(OUT_DIR, 'TCP真实运动_P2P版_station.py')
        it.Save(out2)
        print('exported ->', out2, os.path.getsize(out2), 'bytes')
        break
