# -*- coding: utf-8 -*-
"""清理 + 诊断：1) 找出 AddFile 产生的『机械臂法兰真实运动』重复项并删除（保留旧项）；
2) 对比站内回读代码与磁盘新代码的首个差异位置，判断是否只是规范化差异。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON

OLD = '磨砂圆柱_R180_H40'
NEW = '磨砂圆柱_R150_H50'
DUMP_DIR = None
base = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump'
cands = [d for d in os.listdir(base) if d.startswith('rename_')]
assert cands, '没有 rename_ 目录'
DUMP_DIR = os.path.join(base, sorted(cands)[-1])
print('dump 目录:', DUMP_DIR)

RDK = Robolink()
progs = [p if isinstance(p, str) else p.Name() for p in RDK.ItemList(filter=ITEM_TYPE_PROGRAM_PYTHON)]
dup = [n for n in progs if '机械臂法兰真实运动' in n]
print('相关项:', dup)

# 加载预期新代码
exp = open(os.path.join(DUMP_DIR, '机械臂法兰真实运动.py'), encoding='utf-8').read()

# 找出代码==新代码但名字不等于原名的项（即孤儿新项）
for n in dup:
    it = RDK.Item(n)
    code = it.setParam('Code').replace('<br>', '\n')
    same = (code == exp)
    print('---', n, ' 与预期新代码一致=', same, ' 含新名=', NEW in code, ' 含旧名=', OLD in code)
    if same and OLD not in code:
        it.Delete()
        print('    已删除孤儿新项')

# 再查：原名项还在吗
old_it = RDK.Item('机械臂法兰真实运动')
if old_it.Valid():
    ocode = old_it.setParam('Code').replace('<br>', '\n')
    print('\n原名项仍在：含旧名=', OLD in ocode)
    # 差异诊断：用 dump 里旧名版? dump 存的是替换后的。直接对比站内原项（旧名版）与
    # 预期新代码：先做同样的替换，再找首个差异
    oexp = ocode.replace(OLD, NEW)
    print('替换后与预期新代码长度: %d vs %d' % (len(oexp), len(exp)))
    for i, (a, b) in enumerate(zip(oexp, exp)):
        if a != b:
            lo = max(0, i - 40)
            print('首个差异 @%d:' % i)
            print('  站内替换:', repr(oexp[lo:i + 40]))
            print('  磁盘预期:', repr(exp[lo:i + 40]))
            break
    else:
        if len(oexp) != len(exp):
            print('前缀全同，仅长度差 %d（站内尾部多/少）' % (len(oexp) - len(exp)))
            print('站内尾部:', repr(oexp[-60:]))
            print('磁盘尾部:', repr(exp[-60:]))
        else:
            print('完全一致')
