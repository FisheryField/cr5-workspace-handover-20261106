# -*- coding: utf-8 -*-
"""对照实验：站内 TCP仿真 宏自己的规划器，离线跑轨迹7（只读）。
与用户 GUI 操作等价：姿态退让展开 + 避障检查全开 + 全零起点。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

src = open(r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump\TCP仿真_station_export.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
head = '\n'.join(lines[:stop])
# 提出函数定义区（第82行 GUI 构建之前的函数在 81 行分隔线之前？不——函数区与 GUI 区交错，
# 改用 ast 提取全部顶层函数定义 + 必需全局变量，避开 GUI 代码。
import ast as _ast
ns = {'Robolink': robolink.Robolink, 'robot': robot}
tree = _ast.parse(src)
keep_nodes = []
for node in tree.body:
    if isinstance(node, _ast.FunctionDef):
        keep_nodes.append(node)
    elif isinstance(node, _ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], _ast.Name):
        name = node.targets[0].id
        if name in ('RDK', 'robot'):
            continue  # 自备 RDK/robot
        keep_nodes.append(node)
    elif isinstance(node, (_ast.Import, _ast.ImportFrom, _ast.If)):
        keep_nodes.append(node)
module = _ast.Module(body=keep_nodes, type_ignores=[])
ns['RDK'] = RDK
exec(compile(module, 'tcp_sim_macro_funcs', 'exec'), ns)

def log(msg):
    print('  |', msg)

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json', encoding='utf-8'))
records = ns['_retreat_orientation_records'](records)
print(f'展开后执行点数：{len(records)}')
saved = [0.0] * 6
robot.setJoints(saved)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
try:
    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
    print(f'\n=== TCP仿真规划器：预检通过 {len(plan)} 段 ===')
    for k, st in enumerate(plan, 1):
        print(f"  段{k}: {st['method']:5s} J6={st['joints'][5]:+.1f}° 特异={st['special']}")
except ValueError as exc:
    print(f'\n=== TCP仿真规划器：预检失败 ===\n  {exc}')
