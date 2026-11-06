# -*- coding: utf-8 -*-
"""v14u 落地自检：ast/版本指纹/护栏继承/v14u 新要素——目标锚定到位等待必须落在断连分支可达路径上；v14s/t 旧机制名必须零残留。"""
import ast, io, re

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

ast.parse(src)  # 语法关

# 版本指纹：v14u 唯一，旧版本串全清
assert src.count('v14u-20261013-1059') == 1, 'v14u 版本串应恰出现 1 次'
for old in ('v14t-20261013-1034', 'v14s-20261013-1018', 'v14r-20261013-1002', 'v14q-20261013-0942'):
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

# v14u 新要素：目标锚定到位等待（在断连分支可达路径上）
assert 'def _wait_arrival_then_static(target_joints, max_wait_s=20.0):' in src, '到位等待函数必须在位'
m = re.search(r'^MOVL_ARRIVE_WAIT_S = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 60.0, 'MOVL_ARRIVE_WAIT_S 必须为 60s'
m = re.search(r'^MOVL_ARRIVE_TOL_DEG = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 2.0, 'MOVL_ARRIVE_TOL_DEG 必须为 2.0°'
assert src.count('仍未到位') == 1, '到位超时报错应恰一处'
assert 'MovL 直发等待到位：%.0fs，距目标关节%.2f°，续等（不重发，上限%.0fs）。' in src, '每5s进度日志必须在位'
assert 'MovL 直发到位确认：距目标关节%.2f°（%.1fs），验收继续。' in src, '到位确认日志必须在位'
assert 'err <= MOVL_ARRIVE_TOL_DEG and max(abs(v) for v in fb[1]) < 0.5' in src, '到位判定=位置≤2°且速度<0.5'
# v14s/t 旧机制名必须零残留（唯一例外=LOG_VERSION 历史注释）
body = '\n'.join(l for l in src.split('\n') if not l.startswith('LOG_VERSION'))
for gone in ('expect_motion_from', '_wait_departure_then_static', 'MOVL_START_GRACE_S',
             '_start_joints', '未观测到起步', '起步让位上限'):
    assert gone not in body, gone + ' 旧机制残留（历史注释外）'
# 可达性核心断言：断连分支内 _rt.start() → 到位等待 → 静止护栏 → 完成日志
i_thread = src.index("_rt.start()")
i_wait = src.index('actual, is_static = _wait_arrival_then_static(expect_target)')
i_raise = src.index("raise RuntimeError('驱动报断连后等待%.0fs仍未静止")
i_done = src.index("log('驱动断连但运动已自然完成到位；已重连驱动，继续。')")
assert i_thread < i_wait < i_raise < i_done, '到位等待必须位于断连分支线程启动之后、完成日志之前'
# 断连分支不再用 v14o 短采样窗（唯一残留=直发分支外层快速复核）
assert src.count('_wait_controller_static(samples=3') == 1, '3×0.2s 短窗只允许直发分支外层复核一处'
# None 退化语义
assert 'return _wait_controller_static(max_wait_s=max_wait_s)' in src, 'target_joints=None 必须退化为常规静止确认'
# 调用点：直发传段目标关节（不再发送前采样）
assert src.count("expect_target=step['joints']") == 1, 'MovL 直发调用点必须传段目标关节'

# GUI/标题/banner/日志同步为 v14u
assert 'root.title("RoboDK - 机械臂运动控制（P2P v14u）")' in src, '标题必须同步 v14u'
assert 'v14u 法兰补偿MOVL+到位纠偏' in src, '复选框文案必须同步 v14u'
assert '连续运动（P2P v14u）' in src, 'banner 必须同步 v14u'
assert '【v14u】法兰补偿MOVL开启' in src and '【v14u】法兰补偿MOVL执行段' in src, '开启/指纹日志必须 v14u'
assert 'P{i}：v14u 法兰补偿MOVL' in src and 'P{i}：v14u MovL 直发落点法兰级验收通过' in src, '直发/验收日志必须 v14u'
assert 'v14u 法兰级粗验收未过' in src, '未过报文必须 v14u'

# 规划层零改动旁证
assert '单点 MoveL 改细分执行' in src, '单点 MoveL 细分逻辑必须原样保留'

print('PASS: ast OK; v14u in / t/s/r/q out; 护栏继承; v14u 到位等待下沉断连分支且可达; 旧机制名零残留')
