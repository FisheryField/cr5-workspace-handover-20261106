# -*- coding: utf-8 -*-
"""v14t 落地自检：ast/版本指纹/护栏继承/v14t 新要素——重点：起步让位必须落在断连分支可达路径上（v14s 教训）。"""
import ast, io, re

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

ast.parse(src)  # 语法关

# 版本指纹：v14t 唯一，旧版本串全清
assert src.count('v14t-20261013-1034') == 1, 'v14t 版本串应恰出现 1 次'
for old in ('v14s-20261013-1018', 'v14r-20261013-1002', 'v14q-20261013-0942'):
    assert old not in src, old + ' 旧版本串残留'

# 步长铁律 / 关节阈
m = re.search(r'^LINEAR_SUBSTEP_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 20.0, '步长必须保持 20mm'
m = re.search(r'^MOVE_OFFSET_TOL = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 0.5, 'MOVE_OFFSET_TOL 必须保持 0.5°'

# 继承护栏（v14l 拉黑/防呆/断连护栏/v14o 静默重连）
assert 'MOVL_TRIAL_MAX_MM' not in src, 'v14l 无补偿直发开关不得回归'
assert '拒绝发送驱动 MOVL' in src, 'MoveL 缺途经点防呆必须在位'
assert '仍未静止' in src, '真断连护栏必须在位'
assert '重连失败，停止后续指令' in src, '重连失败护栏必须在位'
assert 'silent_reconnect' in src, '后台重连线程必须在位'
assert "split_moves = False" in src, '长运动分瓣停用状态必须保持'

# v14p/q/r 要素继承
assert re.search(r'^MOVL_DIRECT_MAX_MM = 150', src, re.M), '150mm 段长上限'
assert re.search(r'^MOVL_FLANGE_TOL_MM = 8', src, re.M), '8mm 法兰容差'
assert re.search(r'^MOVL_FLANGE_TOL_DEG = 1', src, re.M), '1° 法兰容差'
assert 'def _movl_flange_accept(joints_now, joints_target):' in src, '法兰验收函数在位'
assert 'real_movldirect_var = tk.BooleanVar(value=False)' in src, '开关默认关'
assert 'robot.setPoseTool(eye(4))' in src and 'robot.setPoseTool(_saved_tool_pose)' in src, '单位工具+finally 恢复'
assert src.count('if require_joints and err > MOVE_OFFSET_TOL:') == 2, '两处关节级校验门必须受 require_joints 控制'
assert src.count('require_joints=False,') == 1, 'require_joints=False 真实调用只允许 MovL 直发一处'
assert "_single_move_settle('MoveJ', step['joints'])" in src, 'MoveJ 收口在位'

# v14t 新要素：让位下沉到断连分支（可达性！）
assert 'def _wait_departure_then_static(start_joints, max_wait_s=20.0):' in src, '让位函数必须在位'
assert 'while time.time() - t0 < MOVL_START_GRACE_S:' in src, '让位等待循环必须在位'
assert src.count('未观测到起步') == 1, '超时未起步报错应恰一处'
assert src.count('起步后等待静止超时') == 0, 'v14s 死代码块必须已删净'
# 可达性核心断言：断连分支内部 _rt.start() → _wait_departure_then_static(expect_motion_from) → 完成日志
i_thread = src.index("_rt.start()")
i_wait = src.index('actual, is_static = _wait_departure_then_static(expect_motion_from)')
i_done = src.index("log('驱动断连但运动已自然完成到位；已重连驱动，继续。')")
i_raise = src.index("raise RuntimeError('驱动报断连后等待%.0fs仍未静止")
assert i_thread < i_wait < i_raise < i_done, '让位调用必须位于断连分支线程启动之后、完成日志之前（v14s 教训：放正常分支=永不执行）'
# 断连分支不再用 v14o 短采样窗（唯一残留=直发分支外层快速复核）
assert src.count('_wait_controller_static(samples=3') == 1, '3×0.2s 短窗只允许直发分支外层复核一处'
# None 退化语义
assert 'return _wait_controller_static(max_wait_s=max_wait_s)' in src, 'start_joints=None 必须退化为常规静止确认'
# 调用点：起点实测 + 传递
assert '_start_joints = _controller_feedback()[0]' in src, '发送前必须实测起点关节'
assert 'expect_motion_from=_start_joints' in src, 'MovL 直发调用点必须传起点'
m = re.search(r'^MOVL_START_GRACE_S = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 6.0, 'MOVL_START_GRACE_S 必须为 6.0s'

# GUI/标题/banner/日志同步为 v14t
assert 'root.title("RoboDK - 机械臂运动控制（P2P v14t）")' in src, '标题必须同步 v14t'
assert 'v14t 法兰补偿MOVL+到位纠偏' in src, '复选框文案必须同步 v14t'
assert '连续运动（P2P v14t）' in src, 'banner 必须同步 v14t'
assert '【v14t】法兰补偿MOVL开启' in src and '【v14t】法兰补偿MOVL执行段' in src, '开启/指纹日志必须 v14t'
assert 'P{i}：v14t 法兰补偿MOVL' in src and 'P{i}：v14t MovL 直发落点法兰级验收通过' in src, '直发/验收日志必须 v14t'
assert 'v14t 法兰级粗验收未过' in src, '未过报文必须 v14t'

# 规划层零改动旁证
assert '单点 MoveL 改细分执行' in src, '单点 MoveL 细分逻辑必须原样保留'

print('PASS: ast OK; v14t in / s/r/q out; 护栏继承; v14t 让位下沉断连分支且可达（线程→让位→静止护栏→完成日志顺序断言）')
