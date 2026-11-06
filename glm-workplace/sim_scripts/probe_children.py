# -*- coding: utf-8 -*-
"""只读：列出圆柱/挡板的子项，确认移动父对象即可带动整体。"""
from robodk.robolink import *

RDK = Robolink()
for name in ('磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    it = RDK.Item(name, ITEM_TYPE_OBJECT)
    if not it.Valid():
        print(name, 'MISSING'); continue
    kids = it.Childs()
    print('%s 子项 %d 个：' % (name, len(kids)))
    for k in kids:
        print('   -', k.Name(), 'type=', k.Type())
# 顶层所有对象（防漏：若三板是同级独立对象会被这里列出）
print('顶层站点对象：')
for it in RDK.ItemList(ITEM_TYPE_OBJECT):
    print('   -', it.Name(), '<- parent:', it.Parent().Name())
