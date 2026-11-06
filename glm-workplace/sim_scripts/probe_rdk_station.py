# -*- coding: utf-8 -*-
# 只读检查：当前 RoboDK 实例打开的站、站内宏清单、机器人条目。
# 不写任何东西，不改站状态。
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_PROGRAM, ITEM_TYPE_PROGRAM_PYTHON, ITEM_TYPE_STATION
ITEM_TYPE_MACRO = ITEM_TYPE_PROGRAM_PYTHON

RDK = Robolink(port=20500)  # 默认 API 端口，连到正在运行的实例
print('RoboDK connected: (Robolink ok, ConnectedState is robot-level)')

# 当前活动站
try:
    st = RDK.ActiveStation()
    print('ActiveStation:', st.Name() if st.Valid() else '(invalid)')
except Exception as e:
    print('ActiveStation query failed:', e)

# 全部站/机器人/宏/程序条目
for t, label in ((ITEM_TYPE_STATION, 'STATION'), (ITEM_TYPE_ROBOT, 'ROBOT'), (ITEM_TYPE_MACRO, 'MACRO'), (ITEM_TYPE_PROGRAM, 'PROGRAM')):
    try:
        items = RDK.ItemList(filter=t)
    except Exception as e:
        print(label, 'list failed:', e)
        continue
    names = [i.Name() for i in items]
    print('%s (%d): %s' % (label, len(names), names))

rob = RDK.Item('', ITEM_TYPE_ROBOT)
print('default robot:', rob.Name() if rob.Valid() else '(none)')
