# -*- coding: utf-8 -*-
"""圆柱改名批量修复 v2：
0) 清理上轮孤儿：『机械臂法兰真实运动』双同名——把含旧名的第一项改名归档，
   留在原名上的即为已替换的新项；
1) 对其余含旧名的宏：导出→替换→【newline='' 精确写盘】→AddFile→旧项归档→
   新项顶名→回读按【归一化换行】比对；
2) TCP仿真 同步磁盘副本（精确字节）。
不保存工作站。"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

OLD = '磨砂圆柱_R180_H40'
NEW = '磨砂圆柱_R150_H50'
DISK_TCPSIM = r'D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py'
DUMP_ROOT = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump'

def norm(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

RDK = Robolink()
ts = time.strftime('%Y%m%d_%H%M%S')
dump_dir = os.path.join(DUMP_ROOT, 'rename2_' + ts)
os.makedirs(dump_dir, exist_ok=True)

# ---- 0) 法兰宏孤儿收养 ----
names = [p if isinstance(p, str) else p.Name() for p in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)]
法兰 = [n for n in names if '机械臂法兰真实运动' == n]
if len(法兰) >= 2 or names.count('机械臂法兰真实运动') >= 2:
    first = RDK.Item('机械臂法兰真实运动')
    fcode = first.setParam('Code').replace('<br>', '\n')
    if OLD in fcode:
        first.setName('机械臂法兰真实运动_改名修复前_' + ts)
        print('[孤儿收养] 旧名项已归档:', first.Name())
        # 现在原名指向的应是新项
        cur = RDK.Item('机械臂法兰真实运动')
        ccode = cur.setParam('Code').replace('<br>', '\n')
        ok = (OLD not in ccode) and (NEW in ccode)
        print('[孤儿收养] 原名现指向新项: 旧名已清=%s 新名在位=%s' % (OLD not in ccode, NEW in ccode))
        if not ok:
            print('!! 孤儿收养异常，停')
            sys.exit(1)
    else:
        print('[孤儿收养] 首项已无旧名（可能已修复过），跳过')

# ---- 1) 其余宏 ----
names = [p if isinstance(p, str) else p.Name() for p in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)]
fixed = []
for name in names:
    it = RDK.Item(name)
    code = it.setParam('Code').replace('<br>', '\n')
    if OLD not in code:
        continue
    new_code = code.replace(OLD, NEW)
    print('--- 修复 %s（%d 处）' % (name, code.count(OLD)))
    path = os.path.join(dump_dir, name + '.py')
    with io.open(path, 'w', encoding='utf-8', newline='') as f:   # 精确字节，不翻译换行
        f.write(new_code)
    new_item = RDK.AddFile(path)
    ncode = new_item.setParam('Code').replace('<br>', '\n')
    if norm(ncode) != norm(new_code):
        print('!! 归一化比对仍不符，中止:', name)
        print('  长度 %d vs %d' % (len(ncode), len(new_code)))
        sys.exit(1)
    it.setName(name + '_改名修复前_' + ts)
    new_item.setName(name)
    final = RDK.Item(name)
    fcode = final.setParam('Code').replace('<br>', '\n')
    ok = (OLD not in fcode) and (NEW in fcode)
    print('    回读: 新名在位=%s 旧名已清=%s  旧项归档=%s' % (NEW in fcode, OLD not in fcode, it.Name()))
    if not ok:
        print('!! 回读失败:', name)
        sys.exit(1)
    fixed.append(name)
    if name == 'TCP仿真':
        with io.open(DISK_TCPSIM, 'w', encoding='utf-8', newline='') as f:
            f.write(ncode)    # 以站内回读为准同步磁盘（字节一致）
        print('    磁盘副本已同步（站内回读字节）:', DISK_TCPSIM)

print('\nDONE：本轮修复 %d 个宏：%s' % (len(fixed), fixed))
