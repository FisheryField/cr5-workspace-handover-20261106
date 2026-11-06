# -*- coding: utf-8 -*-
"""v14s 落地自检：ast/版本指纹/步长/护栏/v14p+q+r 要素继承/v14s 新要素（起步让位）全在位。"""
import ast, io, re

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

ast.parse(src)  # 语法关

# 版本指纹：v14s 唯一，旧版本串全清
assert src.count('v14s-20261013-1018') == 1, 'v14s 版本串应恰出现 1 次'
for old in ('v14r-20261013-1002', 'v14q-20261013-0942', 'v14p-20261012-1832'):
    assert old not in src, old + ' 旧版本串残留'

# 步长铁律
m = re.search(r'^LINEAR_SUBSTEP_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 20.0, '步长必须保持 20mm'

# 继承护栏（v14l 拉黑/防呆/断连护栏/v14o 静默重连）
assert 'MOVL_TRIAL_MAX_MM' not in src, 'v14l 无补偿直发开关不得回归'
assert '拒绝发送驱动 MOVL' in src, 'MoveL 缺途经点防呆必须在位'
assert '仍未静止' in src and '未到位' in src, '真断连护栏必须在位'
assert '重连失败，停止后续指令' in src, '重连失败护栏必须在位'
assert 'silent_reconnect' in src, '后台重连线程必须在位'
assert "split_moves = False" in src, '长运动分瓣停用状态必须保持'
m = re.search(r'^MOVE_OFFSET_TOL = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 0.5, 'MOVE_OFFSET_TOL 必须保持 0.5°'

# v14p/v14q 要素继承
assert re.search(r'^MOVL_DIRECT_MAX_MM = 150', src, re.M), '150mm 段长上限'
assert re.search(r'^MOVL_FLANGE_TOL_MM = 8', src, re.M), '8mm 法兰容差'
assert re.search(r'^MOVL_FLANGE_TOL_DEG = 1', src, re.M), '1° 法兰容差'
assert 'def _movl_flange_accept(joints_now, joints_target):' in src, '法兰验收函数在位'
assert 'real_movldirect_var = tk.BooleanVar(value=False)' in src, '开关默认关'
assert 'robot.setPoseTool(eye(4))' in src and 'robot.setPoseTool(_saved_tool_pose)' in src, '单位工具+finally 恢复'
assert 'v14s 法兰级粗验收未过' in src, '粗验收未过即停报文在位（v14s 前缀）'
assert "_single_move_settle('MoveJ', step['joints'])" in src, 'MoveJ 收口在位（不带 require_joints=False）'
idx_mj = src.index("_single_move_settle('MoveJ', step['joints'])")
assert 'require_joints' not in src[idx_mj:idx_mj + 60], 'MoveJ 收口必须走默认 True'

# v14r 要素继承：require_joints 门禁
assert 'def _single_move_settle(method, target, require_joints=True, expect_motion_from=None):' in src, '签名必须带 require_joints=True + expect_motion_from=None'
assert src.count('if require_joints and err > MOVE_OFFSET_TOL:') == 2, '两处关节级校验门都必须受 require_joints 控制'
assert src.count('require_joints=False,') == 1, 'require_joints=False 真实调用只允许 MovL 直发一处（带尾逗号跨行）'

# v14s 新要素：起步让位
m = re.search(r'^MOVL_START_GRACE_S = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 6.0, 'MOVL_START_GRACE_S 必须为 6.0s'
assert '_start_joints = _controller_feedback()[0]' in src, '发送前必须实测起点关节'
assert 'expect_motion_from=_start_joints' in src, 'MovL 直发调用点必须传起点'
assert '未观测到起步' in src, '超时未起步报错在位'
assert '起步后等待静止超时' in src, '起步后 20s 静止护栏在位'
# 起步判定条件必须在让位循环里（关节离开起点 或 速度非静止阈值）
assert 'zip(_fb[0], expect_motion_from)) > MOVE_OFFSET_TOL' in src, '起步判定必须用关节差 vs 起点'
# 让位循环必须在正常分支（断连分支之后、正常 _wait_controller_static 之前）
i_grace = src.index('if expect_motion_from is not None:')
i_normal = src.index('    actual, is_static = _wait_controller_static()')
assert i_grace < i_normal, '让位循环必须先于正常静止确认'

# GUI/标题/banner 同步为 v14s
assert 'root.title("RoboDK - 机械臂运动控制（P2P v14s）")' in src, '标题必须同步 v14s'
assert 'v14s 法兰补偿MOVL+到位纠偏' in src, '复选框文案必须同步 v14s'
assert '连续运动（P2P v14s）' in src, 'banner 必须同步 v14s'
assert '【v14s】法兰补偿MOVL开启' in src, '开启日志必须 v14s'
assert '【v14s】法兰补偿MOVL执行段出断连/落点指纹' in src, 'except 指纹提示必须 v14s'

# 规划层零改动旁证
assert '单点 MoveL 改细分执行' in src, '单点 MoveL 细分逻辑必须原样保留'

print('PASS: ast OK; v14s in / r/q/p out; step=20.0; 拉黑+护栏+防呆在位; '
      'v14p/q/r 要素继承; v14s 起步让位齐（常量6s/起点实测/让位循环/超时报错/起步后20s护栏）')
