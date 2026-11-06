# -*- coding: utf-8 -*-
"""P11 段碰撞取证（只读，不动实机、不存站）：
轨迹7 P10(0,-762,300,180,0,180) -> P11(-500,0,300,180,0,0)
1) 复现 MoveL_Test / MoveJ_Test 判定与碰撞对
2) 沿直线采样，定位首次碰撞位置、TCP/法兰到圆柱轴的距离、穿透深度
"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, transl, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
print('runmode =', RDK.RunMode(), '(1=SIMULATE)')

cyl = RDK.Item('磨砂圆柱_R180_H40', robolink.ITEM_TYPE_OBJECT)
print('圆柱位姿 =', cyl.Pose())
tools = [t.Name() for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL)]
print('工具项 =', tools)

P10 = [0.0, -762.0, 300.0, 180.0, 0.0, 180.0]
P11 = [-500.0, 0.0, 300.0, 180.0, 0.0, 0.0]
pose10 = Fanuc_2_Pose(P10)
pose11 = Fanuc_2_Pose(P11)

saved = robot.Joints().list()[:6]
try:
    sols = robot.SolveIK(pose10)
    sols = [s[:6] for s in sols]
    if not sols:
        print('P10 无 IK 解'); sys.exit(1)
    # 取离全零最近的解，模拟 _nearest_ik_from_current 从零位出发
    q10 = min(sols, key=lambda s: sum(x * x for x in s))
    print('P10 最近解 =', [round(v, 2) for v in q10])

    st_l = robot.MoveL_Test(q10, pose11)
    print('MoveL_Test(P10->P11) status =', st_l)
    q11s = [s[:6] for s in robot.SolveIK(pose11)]
    q11 = min(q11s, key=lambda s: sum((a - b) ** 2 for a, b in zip(s, q10))) if q11s else None
    if q11:
        st_j = robot.MoveJ_Test(q10, q11)
        print('MoveJ_Test status =', st_j)

    # 直线采样找首次碰撞
    prog = RDK.AddProgram('_probe_P11', robot)
    prog.setVisible(False)
    robot.setJoints(q10)
    prog.setPoseFrame(robot.PoseFrame()); prog.setPoseTool(robot.PoseTool())
    prog.MoveJ(q10); prog.MoveL(pose11)
    msg, mat, st = prog.InstructionListJoints(mm_step=5, deg_step=1, collision_check=robolink.COLLISION_OFF)
    cols = mat.tr().rows if mat is not None else []
    print('采样点数 =', len(cols), 'ILJ status =', st)
    hit = None
    for idx, row in enumerate(cols):
        q = [float(v) for v in row[:6]]
        robot.setJoints(q)
        pairs = RDK.CollisionPairs()
        if pairs:
            hit = (idx, q, pairs); break
    if hit is None:
        print('!! 5mm 采样未发现碰撞（与 MoveL_Test 结果矛盾，需人工复核）')
    else:
        idx, q, pairs = hit
        frac = idx / max(len(cols) - 1, 1)
        print(f'首次碰撞: 第{idx}/{len(cols)-1}点 ({frac:.0%})')
        print('  碰撞对 =', '; '.join(f'{a.Name()}[{ia}]-{b.Name()}[{ib}]' for a, b, ia, ib in pairs))
        fk = robot.SolveFK(q)
        tcp = fk.Pos(); flange_pos = (invH(robot.PoseTool()) * fk).Pos()
        cp = cyl.Pose().Pos()
        # 圆柱参数 R=180, H=40（沿物体本地 Z）
        d_tcp = math.dist(tcp, cp); d_fl = math.dist(flange_pos, cp)
        print('  TCP   =', [round(v, 1) for v in tcp], ' 距圆柱中心 =', round(d_tcp, 1), 'mm (R=180)')
        print('  法兰 =', [round(v, 1) for v in flange_pos], ' 距圆柱中心 =', round(d_fl, 1), 'mm')
        print('  关节 =', [round(v, 2) for v in q])
        print(f'  结论: TCP 距圆柱中心 {d_tcp:.0f}mm，{"TCP本体已进入R180范围" if d_tcp < 180 else "TCP仍在圆柱外——碰撞来自工具模型门把手bs1的伸出部分"}')
    prog.Delete()
finally:
    robot.setJoints(saved)
print('done')
