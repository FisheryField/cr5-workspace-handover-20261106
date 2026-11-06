# -*- coding: utf-8 -*-
"""v14c 规划器离线验证（只读，不起 GUI、不动实机）：
从全零位对轨迹12（=轨迹7 的 Δ+76 新场景版）全录入点做 _plan_continuous_trajectory 预检。
通过标准：返回 plan 且 _verify_obstacle_plan 全绿。
"""
import sys, io, json, types
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

# 从磁盘母本提取规划器相关函数（不执行 GUI 部分）
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
# 找模块级函数/全局定义段：从 import 区之后到 root = tk.Tk() 之前
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
head = '\n'.join(lines[:stop])
# 剔除会创建 Robolink/robot 的行（我们自备）与 tkinter 窗口相关（不应出现在 stop 之前）
ns = {}
exec(compile(head, 'p2p_macro_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))
plan_fn = ns['_plan_continuous_trajectory']
_log_lines = []
def log(msg):
    print('  |', msg)
    _log_lines.append(msg)

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹12.json', encoding='utf-8'))
# 与 GUI _execute_checked_real 完全一致：先做姿态退让展开再规划
records = ns['_retreat_orientation_records'](records)
print(f'展开后执行点数：{len(records)}')
saved = [0.0] * 6
robot.setJoints(saved)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
try:
    plan = plan_fn(records, 500.0, log)
    print(f'\n=== 预检通过：{len(plan)} 段 ===')
    for k, step in enumerate(plan, 1):
        print(f"  段{k}: {step['method']:5s} {step['p2p_note']}  J6={step['joints'][5]:+.1f}°  特异={step['special']}")
except ValueError as exc:
    print('\n=== 预检失败 ===')
    print(' ', exc)
    sys.exit(1)
