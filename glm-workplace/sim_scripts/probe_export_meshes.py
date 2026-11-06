# -*- coding: utf-8 -*-
"""只读导出：把站内 地面/圆柱/安装台 对象网格导出为 STL（新增文件，不改站、不保存工作站），
用于核对真实几何包围盒。"""
from robodk.robolink import *
import os

RDK = Robolink()
out_dir = r'D:\mydata\glm-workplace\tools'
pairs = [
    ('地面_禁止穿越', os.path.join(out_dir, 'probe_gnd_station.stl')),
    ('磨砂圆柱_R150_H50', os.path.join(out_dir, 'probe_cyl_station.stl')),
    ('安装台_650x650x80mm', os.path.join(out_dir, 'probe_table_station.stl')),
]
for name, path in pairs:
    it = RDK.Item(name, ITEM_TYPE_OBJECT)
    if not it.Valid():
        print(name, 'MISSING')
        continue
    if os.path.exists(path):
        os.remove(path)
    it.Save(path)
    print('exported', name, '->', path, os.path.getsize(path), 'bytes')
