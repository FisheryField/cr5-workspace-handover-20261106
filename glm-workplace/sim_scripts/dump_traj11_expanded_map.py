# -*- coding: utf-8 -*-
"""轨迹11 展开映射表（只读）：打印 25 个执行点的来源（对应第几个录入点 / 退让插入点）、
TCP 值与奇异标志——用于把 P23/P20 等失败标签翻译回轨迹源里的具体点。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)

recs = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹11.json', encoding='utf-8'))
expanded = ns['_retreat_orientation_records'](recs)
print('执行点 %d 个（录入 %d 个）' % (len(expanded), len(recs)))
for i, e in enumerate(expanded, 1):
    v = e['values']
    lab = e.get('label', '')
    kind = '奇异' if e.get('singular') else '  '
    delta = e.get('j6_delta', 0)
    # 判断是否=某录入点原值
    rec_idx = None
    for r, rec in enumerate(recs, 1):
        if all(abs(a - b) < 1e-6 for a, b in zip(v, rec['values'])):
            rec_idx = r
            break
    print('执行P%-2d %s d=%+4d  录入#%-2s  %-14s  TCP=[%7.1f %8.1f %6.1f | %6.1f %5.1f %6.1f]'
          % (i, kind, delta, rec_idx if rec_idx else '-', lab,
             v[0], v[1], v[2], v[3], v[4], v[5]))
