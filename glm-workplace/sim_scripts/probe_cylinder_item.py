# -*- coding: utf-8 -*-
"""只读：列出站内所有含「圆柱」/cylinder 的对象及其位姿、父级、包围盒。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Pose_2_Fanuc

RDK = robolink.Robolink()
items = RDK.ItemList()
# ItemList 在本环境返回 Item 对象列表（个别版本返回名字字符串）
def _nm(x):
    return x if isinstance(x, str) else x.Name()
hits = [x for x in items if ('圆柱' in _nm(x)) or ('cylinder' in _nm(x).lower())]
print('命中对象：', [_nm(x) for x in hits])
for x in hits:
    it = x if not isinstance(x, str) else RDK.Item(x)
    if not it.Valid():
        continue
    n = it.Name()
    p = it.Pose()
    pos = p.Pos()
    par = it.Parent()
    f = Pose_2_Fanuc(p)
    print('---', n)
    print('   type=', it.Type(), ' parent=', par.Name() if par.Valid() else '(station root)')
    print('   pose pos=(%.3f, %.3f, %.3f) rot_deg=(%.2f, %.2f, %.2f)' % (
        pos[0], pos[1], pos[2], f[3], f[4], f[5]))
    bbm = [m for m in dir(it) if 'ound' in m or 'geom' in m.lower() or 'geom' in m]
    print('   可用几何方法:', bbm)
    try:
        g = it.Geometry()
        print('   Geometry type:', type(g))
        if isinstance(g, (list, tuple)):
            print('   Geometry pts:', len(g))
    except Exception as e:
        print('   Geometry() ->', e)
