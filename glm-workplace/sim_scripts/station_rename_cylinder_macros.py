# -*- coding: utf-8 -*-
"""站内宏批量修复：凡引用『磨砂圆柱_R180_H40』的 Python 宏，精确替换为
『磨砂圆柱_R150_H50』（用户已改站内对象名）。流程：导出源码 → 校验替换数 →
AddFile 新项 → 旧项改名归档（…_改名修复前_TS）→ 新项顶回原名 → 回读校验。
『TCP仿真』同时把新源码同步到磁盘副本 机械臂TCP仿真_副本.py。
不保存工作站、不碰控制器。"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

OLD = '磨砂圆柱_R180_H40'
NEW = '磨砂圆柱_R150_H50'
DISK_TCPSIM = r'D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py'
DUMP_ROOT = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump'

RDK = Robolink()
ts = time.strftime('%Y%m%d_%H%M%S')
dump_dir = os.path.join(DUMP_ROOT, 'rename_' + ts)
os.makedirs(dump_dir, exist_ok=True)

progs = RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)
names = [p if isinstance(p, str) else p.Name() for p in progs]
print('站内宏：', names)

fixed = []
for name in names:
    it = RDK.Item(name)
    code = it.setParam('Code').replace('<br>', '\n')
    if OLD not in code:
        continue
    n = code.count(OLD)
    new_code = code.replace(OLD, NEW)
    assert OLD not in new_code
    print('--- 修复 %s（%d 处）' % (name, n))
    path = os.path.join(dump_dir, name + '.py')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_code)
    new_item = RDK.AddFile(path)
    ncode = new_item.setParam('Code').replace('<br>', '\n')
    if ncode != new_code:
        print('!! 新项代码与预期不符，中止（保留旧项原名）:', name)
        sys.exit(1)
    it.setName(name + '_改名修复前_' + ts)
    new_item.setName(name)
    final = RDK.Item(name)
    fcode = final.setParam('Code').replace('<br>', '\n')
    ok = (OLD not in fcode) and (NEW in fcode)
    print('    回读: 原名在位=%s 新名已入=%s 旧名已清=%s  归档为=%s' % (
        final.Valid(), NEW in fcode, OLD not in fcode, it.Name()))
    if not ok:
        print('!! 回读失败:', name)
        sys.exit(1)
    fixed.append(name)
    if name == 'TCP仿真':
        with open(DISK_TCPSIM, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print('    磁盘副本已同步:', DISK_TCPSIM, len(new_code), '字符')

print('\nDONE：已修复 %d 个宏：%s' % (len(fixed), fixed))
if not fixed:
    print('（没有宏再引用旧名）')
