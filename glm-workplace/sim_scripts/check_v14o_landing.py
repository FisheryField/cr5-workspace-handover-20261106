# -*- coding: utf-8 -*-
"""v14o 落地自检：ast/版本指纹/步长/护栏（MOVL 拉黑+断连护栏）全在位。"""
import ast, io, re, sys

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

ast.parse(src)  # 语法关

# 版本指纹：v14o 唯一，v14n/v14m 不残留（注释中提及除外——本次版本串注释只含 v14o）
assert src.count("v14o-20261012-1747") == 1, 'v14o 版本串应恰出现 1 次'
assert 'v14n-20261012-1712' not in src, 'v14n 旧版本串残留'
assert 'v14m-20261012-1645' not in src, 'v14m 旧版本串残留'

# 步长铁律
m = re.search(r'^LINEAR_SUBSTEP_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 20.0, '步长必须保持 20mm'

# v14l 拉黑护栏 + 断连护栏
assert 'MOVL_TRIAL_MAX_MM' not in src, 'v14l 直发开关不得回归'
assert '拒绝发送驱动 MOVL' in src, 'MoveL 缺途经点防呆必须在位'
assert '仍未静止' in src and '未到位' in src, '真断连护栏（静止上限/到位校验）必须在位'
assert '重连失败，停止后续指令' in src, '重连失败护栏必须在位'

# v14o 静默重连要素
assert 'silent_reconnect' in src, '后台重连线程必须在位'
assert '_wait_controller_static(samples=3, interval=0.2)' in src, '断连分支快速静止采样必须在位'
assert src.count('time.sleep(1.5)') == 0, '恢复场景固定 1.5s sleep 应已移除'

# 分瓣直发禁令不变
assert "split_moves = False" in src, '长运动分瓣停用状态必须保持'

print('PASS: ast OK; v14o in / v14n+m out; step=20.0; MOVL+disconnect guardrails present; silent-reconnect in place')
