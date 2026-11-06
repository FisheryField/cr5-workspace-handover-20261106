# -*- coding: utf-8 -*-
# 按用户指令：向当前 RoboDK 站内新增宏 'TCP真实运动_P2P版'（AddFile 会嵌入一份拷贝）。
# 不改既有宏、不保存工作站。
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

SRC = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
RDK = Robolink()

existing = [it.Name() for it in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)]
if 'TCP真实运动_P2P版' in existing:
    print('SKIP: 站内已存在 TCP真实运动_P2P版，不重复添加。')
else:
    item = RDK.AddFile(SRC)
    print('added:', item.Name(), 'valid:', item.Valid())

# 验证：重新列出宏清单
names = [it.Name() for it in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)]
print('macro count now:', len(names))
print('has P2P:', 'TCP真实运动_P2P版' in names)
