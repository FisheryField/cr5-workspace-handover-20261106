# -*- coding: utf-8 -*-
"""v14w 落地自检（只读源码断言 + ast.parse）。用法：
  python check_v14w_landing.py
PASS=0 / FAIL=1。断言清单：
  1) ast.parse 全文件通过；LOG_VERSION=v14w。
  2) _movl_digit_safe_joints 已定义，含三边界（x/rx/rz）与 0.05° 上限。
  3) 直发链路：purge 先于自算法兰位姿先于直发；实发 _send_q 衍生位姿；expect_target=step['joints']（认证关节）。
  4) 净化失败 ⇒ direct_ready=False 且存在通往细分的 elif（安全回落可达——顺序断言）。
  5) MOVL_DIRECT_BLOCK_POINTS = ()（恢复 P9 直发）。
  6) 验收/收口仍对 step['joints']（净化不改验收对象）。
  7) 版本标识三处（LOG_VERSION/root.title/开启 banner）均为 v14w。
"""
import ast, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = open(PATH, encoding='utf-8').read()
fails = []

def check(name, cond, detail=''):
    tag = 'PASS' if cond else 'FAIL'
    print('[%s] %s%s' % (tag, name, (' — ' + detail) if (detail and not cond) else ''))
    if not cond:
        fails.append(name)

# 1
try:
    ast.parse(src)
    check('ast.parse', True)
except SyntaxError as e:
    check('ast.parse', False, str(e))
check('LOG_VERSION v14w41', "LOG_VERSION = 'v14w41-20261027-toolfix'" in src)
check('v14w30 到位阈5°', 'MOVL_ARRIVE_TOL_DEG = 5.0' in src and 'MOVL_ARRIVE_TOL_DEG = 2.0' not in src)
check('v14w31 已撤回（无稳定窗）', '_post_reconnect_stabilize' not in src)
check('v14w32 J6换同角表示', '换同角表示 {_j6n:.3f}°' in src and 'copysign(359.999' not in src
      and 'end[5] - math.copysign(360.0, end[5])' in src)
check('v14w33 换姿段MoveJ直达', '同位姿换姿MoveJ直达' in src and '_seg_mm_ro <= 1.0' in src)
check('v14w33b 救援换姿前视', '下一点为同位姿换姿' in src and '_nxt_pose' in src)
check('v14w33c 回撤段让位', '_reorient_next_pose' in src and '回撤段且下一点为同位姿换姿' in src)
check('v14w33d 回改上一步分支', '回改上一步分支后' in src and "_prev_step['joints'] = c6[:]" in src)
check('v14w34 真位置差判据', '_seg_mm_ro = math.sqrt(sum' in src
      and 'norm((_trajectory_pose(q) * invH(target)).Pos())' not in src)
check('v14w35 门禁210', 'MOVL_DIRECT_MAX_MM = 210.0' in src
      and 'MOVL_DIRECT_MAX_MM = 150.0' not in src)
check('实机限位常量（v14w23 J4=150）', 'REAL_JOINT_LIMITS = (180.0, 180.0, 160.0, 150.0, 180.0, 360.0)' in src)
check('v14w23 自干涉注释', 'J4=-189.70 被控制器 -40004' in src)
check('短直线强制MoveL', '短直线强制MoveL' in src and '不尝试 MoveJ 弧' in src)
check('v14w24 默认开启无勾选框', 'real_movldirect_var = tk.BooleanVar(value=True)' in src
      and 'v14u 法兰补偿MOVL+到位纠偏' not in src
      and src.count('real_movldirect_var') >= 2)
check('v14w25 降速10', 'ROBOT_SPEED = 10.0' in src and '10 mm/s' in src)
check('v14w25 J6边界内推', src.count('359.999') >= 3 and '-40006' in src)
check('v14w26 组合禁区', 'REAL_INTERFERE_J4_MAX = 100.0' in src
      and 'REAL_INTERFERE_J5_MIN = 165.0' in src
      and src.count('_real_interfere_combo(') >= 3)
check('限位过滤调用≥5处', src.count('_real_limit_ok(') >= 5)
check('取近表示补限位复核', src.count('# v14w22：取近表示必须复核实机限位') == 2)
check('执行前最后防线', '目标关节超出实机限位' in src)
check('受控补发存在', '补发一次（v14w20）' in src and src.count('补发一次（v14w20）') == 2)
check('三角离零域防御', 'for v in (rx, ry, rz):' in src and 'abs(v) < 0.001' in src)
check('6位小数定型', "float('%.6f' % v)" in src)
check('rz+180 越界防御存在', 'rz >= 179.999' in src)
# v14w17 工具守护：定义1次+调用2次（启动+执行入口）
check('工具守护含启动、入口和空闲', src.count('_ensure_canonical_tool()') >= 5)
check('规范工具常量 v14w40=126', 'CANONICAL_TOOL = (0.0, 0.0, 126.0, 0.0, 0.0, 0.0)' in src)
check('守护恢复值=126', '已自动恢复 [0,0,126]' in src and '已自动恢复 [0,0,100]' not in src)
check('把手按名并入配对循环', "_handle = RDK.Item('门把手_bs1')" in src and 'tool_items.append(_handle)' in src)
# v14w39：窗口=包装层覆盖整个 settle + 守卫恢复把手 + 模型钉终点
check('v14w41 独立法兰工具窗口', 'def _settle_core(' in src
      and 'flange_space 时单位变换+藏把手覆盖' in src
      and 'robot.setPoseTool(eye(4))' not in src
      and 'robot.setPoseTool(_flange_tool)' in src
      and src.count('_win_handle.setVisible(False)') == 1
      and '_win_handle.setVisible(_win_visible)' in src
      and 'movl_identity_tool' not in src)
check('v14w39 守卫恢复把手', "RDK.Item('门把手_bs1')" in src
      and '_gh.Visible()' in src and '_gh.setVisible(True)' in src)
check('v14w39 模型钉终点', "robot.setJoints(step['joints'])" in src)
check('v14w37 直发传法兰位姿', '_send_pose = invH(robot.PoseFrame()) * robot.SolveFK(_send_q)' in src
      and "_single_move_settle('MoveL', _send_pose" in src)

# 1b 半封闭3面挡板 + 圆柱新名登记（v14w8）；旧实心挡板与旧圆柱名已清除
check('障碍物清单含半封闭挡板', "'挡板_半封闭3面'" in src
      and "('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面')" in src)
check('旧实心挡板名不在宏内', '挡板_215x710x20' not in src)
check('旧圆柱名不在宏内', '磨砂圆柱_R180_H40' not in src)

# 2
check('净化函数已定义', 'def _movl_digit_safe_joints(' in src)
check('净化-x边界', '-0.01 < x < 0.001' in src)
check('净化-rx边界', '89.999 <= rx <= 90.001' in src)
check('净化-三角离零域', 'for v in (rx, ry, rz):' in src)
check('净化-单关节≤0.05°', '> 0.05 + 1e-9' in src)
check('净化-失败返回None', "return None, '发送位姿净化失败" in src)

# 3 直发链路顺序（v14w36：净化 → 自算法兰位姿 → 直发调用）
i_purge = src.find('_send_q, _purge_note = _movl_digit_safe_joints(')
i_pose = src.find('_send_pose = invH(robot.PoseFrame()) * robot.SolveFK(_send_q)', i_purge)
i_send = src.find("_single_move_settle('MoveL', _send_pose,", i_purge)
check('净化先于位姿化先于直发调用', 0 < i_purge < i_pose < i_send)
check('实发 _send_q 衍生位姿', i_send > i_purge and i_pose > i_purge)
check('expect_target=step[joints]', "expect_target=step['joints']" in src[i_send:i_send + 300])

# 4 安全回落：purge 失败置 direct_ready=False，其后存在 elif waypoints 分支
i_fail = src.find("direct_ready = False")
i_elif_wp = src.find('elif waypoints:', i_purge)
check('净化失败置 direct_ready=False', i_fail > i_purge)
check('细分 elif 在直发链之后可达', i_elif_wp > i_send)

# 5
check('禁直发名单已清空', 'MOVL_DIRECT_BLOCK_POINTS = ()' in src)
check('名单=() 无残留 (9,)', 'MOVL_DIRECT_BLOCK_POINTS = (9,)' not in src)

# 6 验收/收口对象
i_accept = src.find('_movl_flange_accept(_actual, step[\'joints\'])')
check('法兰验收仍对认证关节', i_accept > 0)
check('MoveJ 收口仍对认证关节', "_single_move_settle('MoveJ', step['joints'])" in src)

# 7 三处版本
check('root.title v14w41', 'P2P v14w41' in src and 'P2P v14w40' not in src)
check('开启 banner v14w41', '【v14w41】法兰补偿MOVL默认开启' in src and '【v14w40】' not in src
      and '工具=126mm' in src)
check('无残留【v14v4】banner', '【v14v4】' not in src)
check('直发注释工具=182', '物理工具尖端（182mm，v14w27 实测）' in src and '100mm，v14w14 取整' not in src)
check('网格注释=v4 手术（把手端182）', '把手组件外移、工作点 z=182' in src and '待加长至 182' not in src)
check('场景注释=v14w29 实测包络', 'Y[−1062,−782]' in src and '(0,-926,300)' not in src)

print()
print('RESULT:', 'PASS' if not fails else 'FAIL -> ' + ', '.join(fails))
sys.exit(0 if not fails else 1)
