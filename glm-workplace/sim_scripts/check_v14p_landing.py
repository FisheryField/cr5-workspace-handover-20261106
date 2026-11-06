# -*- coding: utf-8 -*-
"""v14p 落地自检：ast/版本指纹/步长/护栏（MOVL拉黑+断连护栏+v14l防呆）/v14p 新要素全在位。"""
import ast, io, re

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

ast.parse(src)  # 语法关

# 版本指纹：v14p 唯一，v14o/v14n/v14m 全版本串不残留
assert src.count('v14p-20261012-1832') == 1, 'v14p 版本串应恰出现 1 次'
assert 'v14o-20261012-1747' not in src, 'v14o 旧版本串残留'
assert 'v14n-20261012-1712' not in src, 'v14n 旧版本串残留'
assert 'v14m-20261012-1645' not in src, 'v14m 旧版本串残留'

# 步长铁律
m = re.search(r'^LINEAR_SUBSTEP_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 20.0, '步长必须保持 20mm'

# v14l 无补偿直发拉黑 + 防呆 + 断连护栏
assert 'MOVL_TRIAL_MAX_MM' not in src, 'v14l 无补偿直发开关不得回归'
assert '拒绝发送驱动 MOVL' in src, 'MoveL 缺途经点防呆必须在位'
assert '仍未静止' in src and '未到位' in src, '真断连护栏（静止上限/到位校验）必须在位'
assert '重连失败，停止后续指令' in src, '重连失败护栏必须在位'

# v14o 静默重连要素（继承）
assert 'silent_reconnect' in src, '后台重连线程必须在位'
assert '_wait_controller_static(samples=3, interval=0.2)' in src, '断连分支快速静止采样必须在位'
assert src.count('time.sleep(1.5)') == 0, '恢复场景固定 1.5s sleep 应已移除'
assert "split_moves = False" in src, '长运动分瓣停用状态必须保持'

# v14p 法兰补偿MOVL 新要素
m = re.search(r'^MOVL_DIRECT_MAX_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 150.0, 'v14p 段长上限 150mm'
assert 'real_movldirect_var = tk.BooleanVar(value=False)' in src, 'v14p 开关必须默认关'
assert 'def _movl_direct_ready():' in src, '开关就绪探测（离线 verify 安全）必须在位'
assert 'robot.setPoseTool(eye(4))' in src, '发送瞬间工具置单位变换（补偿核心）必须在位'
assert 'robot.setPoseTool(_saved_tool_pose)' in src, 'finally 恢复工具必须在位'
assert "math.radians(0.5)" in src, '姿态恒定≤0.5° 门禁必须在位'
# 分支门禁顺序：movl_direct 在前（开关关时不算段长）
assert 'if (movl_direct and seg_mm is not None' in src, '直发分支必须先看开关再看段长'
# 段长计算入口也要先看开关
assert "if movl_direct and step['method'] == 'MoveL' and waypoints:" in src, '段长计算必须开关开启才执行'
# 直发目标仍是本步终点关节（终点构型 0.5° 校验天然罩住）
assert "_single_move_settle('MoveL', step['joints'])" in src, '直发目标必须是预检终点关节'
# 失败指纹提示（v14l 同款）
assert '建议去勾回退' in src, '失败指纹提示必须在位'

# 规划层零改动旁证：单点 MoveL 细分逻辑原样
assert '单点 MoveL 改细分执行' in src, '单点 MoveL 细分逻辑必须原样保留'

print('PASS: ast OK; v14p in / v14o+n+m out; step=20.0; MOVL拉黑+断连护栏+防呆在位; '
      '法兰补偿MOVL要素齐（默认关/单位工具/finally恢复/0.5°姿态门禁/150mm上限）')
