# -*- coding: utf-8 -*-
"""转储展开后的 17 个执行点（只读）。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json', encoding='utf-8'))
ex = ns['_retreat_orientation_records'](records)
for k, r in enumerate(ex, 1):
    print(f"E{k:2d} {r.get('label','?'):12s} {r['values']}{'  sing' if r.get('singular') else ''}{'  require_linear' if r.get('require_linear') else ''}")
