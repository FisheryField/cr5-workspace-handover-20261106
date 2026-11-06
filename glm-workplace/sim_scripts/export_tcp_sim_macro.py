# -*- coding: utf-8 -*-
"""导出站内 TCP仿真 宏源码，核查其是否做碰撞检查（只读取证）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
out = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump\TCP仿真_station_export.py'
macro = RDK.Item('TCP仿真', robolink.ITEM_TYPE_PROGRAM_PYTHON)
assert macro.Valid(), '未找到站内宏 TCP仿真'
macro.Save(out)
src = open(out, encoding='utf-8', errors='replace').read()
print('exported bytes:', len(src))
for kw in ('MoveL_Test', 'MoveJ_Test', 'InstructionListJoints', 'collision_check', 'setCollisionActive', 'CollisionPairs', 'LOG_VERSION'):
    hits = [i + 1 for i, l in enumerate(src.splitlines()) if kw in l]
    print(f'{kw}: {len(hits)} 处 {hits[:8]}')
