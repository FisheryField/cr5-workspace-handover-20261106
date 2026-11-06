# -*- coding: utf-8 -*-
"""场景当前值确认 + 圆柱抬80后的最近工作点解算与可达验证。
几何：滚轮中心 (0,-886,z_c)，赤道面 y=-736；面贴合 TCP 外伸取实测 2.0mm → y=-734。
验证：正解姿态 (0,-90,180) 在 (0,-734,460) 的 IK + 位姿碰撞。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
cyl = RDK.Item('磨砂圆柱_R150_H50')
p = Pose_2_Fanuc(cyl.Pose())
print('当前滚轮 pose = (%.1f, %.1f, %.1f)' % (p[0], p[1], p[2]))
print('（若你要的是"抬80后"：中心 (0,-886,460)，赤道面 y=-736 @ z=460）')

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
from_fanuc = ns['fanuc_values_to_pose']
ns['_ensure_canonical_tool']()
print('PoseTool =', robot.PoseTool().Pos())

def test(name, x, y, z, rx, ry, rz):
    T = from_fanuc(x, y, z, rx, ry, rz)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        print('%s -> 无解' % name)
        return
    q = [float(v) for v in s[0][:6]]
    RDK.setRunMode(robolink.RUNMODE_SIMULATE)
    hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
    print('%s -> %d解；位姿%s；关节=%s' % (
        name, len(s), '碰撞!' if hit else '无碰撞', ['%.2f' % v for v in q]))
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)

# 赤道最前点 + 面贴合 TCP（外伸2.0 / 保守按壳面12.3 各测）
test('贴合TCP(外伸2.0) (0,-734,460, 0,-90,180)', 0.0, -734.0, 460.0, 0.0, -90.0, 180.0)
test('壳面深度(外伸12.3) (0,-723.7,460, 0,-90,180)', 0.0, -723.7, 460.0, 0.0, -90.0, 180.0)
print('DONE')
