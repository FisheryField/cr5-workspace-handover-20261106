# -*- coding: utf-8 -*-
"""probe_station_items_1013.py — RoboDK 重启后站内完整性探针（只读）
检查：Dobot CR5 / 门把手_bs1 工具 / 磨砂圆柱_R180_H40 / 台子·地面 / 参考系 / 宏
"""
from robolink import Robolink

RDK = Robolink()
print('=== 全站 item 清单 ===')
items = RDK.ItemList()
ok = {}
for it in items:
    try:
        name = it.Name()
        t = it.Type()
    except Exception:
        continue
    type_name = {1: 'frame', 2: 'robot', 3: 'tool', 5: 'object', 7: 'program',
                 8: 'station', 10: 'macro', 11: 'python'}.get(t, str(t))
    print('  [%s] %s' % (type_name, name))
    ok[name] = (it, type_name)

print()
print('=== 关键项检查 ===')
for key, want in [('Dobot CR5', 'robot'), ('门把手_bs1', 'tool'),
                  ('磨砂圆柱_R180_H40', 'object'), ('台子', 'object'), ('地面', 'object')]:
    hit = [n for n in ok if key in n]
    print('%s: %s' % (key, hit if hit else '!! 缺失'))

print()
print('=== 活动站与宏 ===')
st = RDK.ActiveStation()
print('活动站:', st.Name())
macros = [n for n, (i, t) in ok.items() if t in ('macro', 'python')]
print('宏/脚本:', macros)
