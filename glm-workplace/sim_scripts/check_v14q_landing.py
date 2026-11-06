# -*- coding: utf-8 -*-
"""v14q 落地自检：ast/版本指纹/步长/护栏（MOVL拉黑+断连护栏+v14l防呆）/v14p 要素继承/v14q 新要素全在位。"""
import ast, io, re

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

ast.parse(src)  # 语法关

# 版本指纹：v14q 唯一，旧版本串全清
assert src.count('v14q-20261013-0942') == 1, 'v14q 版本串应恰出现 1 次'
for old in ('v14p-20261012-1832', 'v14o-20261012-1747', 'v14n-20261012-1712', 'v14m-20261012-1645'):
    assert old not in src, old + ' 旧版本串残留'

# 步长铁律
m = re.search(r'^LINEAR_SUBSTEP_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 20.0, '步长必须保持 20mm'

# v14l 无补偿直发拉黑 + 防呆 + 断连护栏（继承）
assert 'MOVL_TRIAL_MAX_MM' not in src, 'v14l 无补偿直发开关不得回归'
assert '拒绝发送驱动 MOVL' in src, 'MoveL 缺途经点防呆必须在位'
assert '仍未静止' in src and '未到位' in src, '真断连护栏（静止上限/到位校验）必须在位'
assert '重连失败，停止后续指令' in src, '重连失败护栏必须在位'

# v14o 静默重连要素（继承）
assert 'silent_reconnect' in src, '后台重连线程必须在位'
assert '_wait_controller_static(samples=3, interval=0.2)' in src, '断连分支快速静止采样必须在位'
assert src.count('time.sleep(1.5)') == 0, '恢复场景固定 1.5s sleep 应已移除'
assert "split_moves = False" in src, '长运动分瓣停用状态必须保持'

# v14p 法兰补偿MOVL 要素（继承）
m = re.search(r'^MOVL_DIRECT_MAX_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 150.0, 'v14p 段长上限 150mm'
assert 'real_movldirect_var = tk.BooleanVar(value=False)' in src, '开关必须默认关'
assert 'def _movl_direct_ready():' in src, '开关就绪探测（离线 verify 安全）必须在位'
assert 'robot.setPoseTool(eye(4))' in src, '发送瞬间工具置单位变换（补偿核心）必须在位'
assert 'robot.setPoseTool(_saved_tool_pose)' in src, 'finally 恢复工具必须在位'
assert "math.radians(0.5)" in src, '姿态恒定≤0.5° 门禁必须在位'
assert 'if (movl_direct and seg_mm is not None' in src, '直发分支必须先看开关再看段长'
assert "if movl_direct and step['method'] == 'MoveL' and waypoints:" in src, '段长计算必须开关开启才执行'
assert "_single_move_settle('MoveL', step['joints'])" in src, '直发目标必须是预检终点关节'

# v14q 新要素：法兰级粗验收 + MoveJ 微纠偏收口
m = re.search(r'^MOVL_FLANGE_TOL_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 8.0, 'v14q 法兰位置容差 8mm'
m = re.search(r'^MOVL_FLANGE_TOL_DEG = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 1.0, 'v14q 法兰姿态容差 1.0°'
assert 'def _movl_flange_accept(joints_now, joints_target):' in src, '法兰验收函数必须在位'
# 验收在工具恢复之后（语义正确：恢复后的 FK 无需单位工具，函数内部不加 PoseTool）
i_accept_fn = src.index('def _movl_flange_accept')
i_settle = src.index("_single_move_settle('MoveL', step['joints'])")
i_restore = src.index('robot.setPoseTool(_saved_tool_pose)')
assert i_accept_fn < i_settle < i_restore, '验收函数定义在直发分支之前'
# 直发分支内：粗验收调用在 finally 恢复之后
i_call = src.index('_actual, _is_static = _wait_controller_static(samples=3, interval=0.2)')
assert i_restore < i_call, '法兰粗验收必须在工具恢复之后调用'
# 粗验收不过即停（真异常），过了才可能发 MoveJ 纠偏
assert 'v14q 法兰级粗验收未过' in src, '粗验收未过即停报文必须在位'
assert "if _jm > MOVE_OFFSET_TOL:" in src, '仅关节残差超 0.5° 时才发 MoveJ 微纠偏'
assert "_single_move_settle('MoveJ', step['joints'])" in src, 'MoveJ 微纠偏收口必须在位'
assert "_require_joints(step['joints'])" in src, '终点关节级校验必须保留'
# except 指纹行扩展了粗验收关键词
assert "'粗验收' in str(exc)" in src, 'except 指纹行必须含粗验收关键词'
# 关节级 0.5° 校验没有被放宽（MOVE_OFFSET_TOL 仍 0.5，且 MovL 直发段终点仍由它罩住）
m = re.search(r'^MOVE_OFFSET_TOL = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 0.5, 'MOVE_OFFSET_TOL 必须保持 0.5°'

# 规划层零改动旁证：单点 MoveL 细分逻辑原样
assert '单点 MoveL 改细分执行' in src, '单点 MoveL 细分逻辑必须原样保留'

# GUI/标题/banner 同步为 v14q
assert 'root.title("RoboDK - 机械臂运动控制（P2P v14q）")' in src, '标题必须同步 v14q'
assert 'v14q 法兰补偿MOVL+到位纠偏' in src, '复选框文案必须同步 v14q'
assert '连续运动（P2P v14q）' in src, 'banner 必须同步 v14q'

print('PASS: ast OK; v14q in / p/o/n/m out; step=20.0; 拉黑+护栏+防呆在位; '
      'v14p 要素继承; v14q 新要素齐（8mm/1° 粗验收+MoveJ 收口+0.5° 未放宽+指纹扩展）')
