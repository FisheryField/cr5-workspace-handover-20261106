# -*- coding: utf-8 -*-
"""11:04 场 P9 段离线复算（只读，不起 GUI、不动实机）：
复现 11:03:36 入口的完整规划（11 点全量+姿态退让），打印 17 段各自目标关节；
再算 P8 目标与 P9 目标（=MovL 直发步的 target_joints）的关节差——
用于核对实机日志「P9 停时距目标 10.69° / J2 -10.0 / J3 -20.0」是否与规划一致。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)
robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
plan = ns['_plan_continuous_trajectory'](records, 500.0, lambda m: None)
print(f'段数={len(plan)}')
for k, step in enumerate(plan, 1):
    print(f"段{k:2d}: {step['method']:5s} {step['p2p_note'][:44]:44s} joints=" + ','.join(f'{v:+9.4f}' for v in step['joints']))

j8 = plan[7]['joints']
j9 = plan[8]['joints']
diff = [b - a for a, b in zip(j8, j9)]
print('\nP8(段8) 目标 =', [round(v, 4) for v in j8])
print('P9(段9) 目标 =', [round(v, 4) for v in j9])
print('P9−P8 关节差 =', [round(v, 4) for v in diff])
print('最大差 =', round(max(abs(v) for v in diff), 4))
