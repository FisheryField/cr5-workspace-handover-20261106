# -*- coding: utf-8 -*-
"""P9 迟到落点身份鉴定（只读：只 SolveFK/Pose_2_Fanuc，不 setJoints、不改 runmode、不发指令）。

把 J_LAND=[-63.41,-13.45,-66.65,-69.89,-63.41,0] 的 TCP(FK*tool) 与法兰(FK)
换算成 Fanuc 值，与轨迹源 11 个录入点逐一对照；同时打印 P4/P5/P8/P9 的 TCP 作锚。
再测：J_LAND 的 TCP 是否等于某个录入点；J_LAND 的法兰是否等于 FK(P9)*tool 等。
"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH, norm, pose_angle, Fanuc_2_Pose, Pose_2_Fanuc

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
tool = robot.PoseTool()

J = {
    'P8(起点)':   [-63.41392174214573, -23.452600702069333, -86.65404121903774,
                   -69.89335807889292, -63.41392174214573, 0.0],
    'P9(目标)':   [-74.10620847168758, -22.194417181878357, -88.53508496756278,
                   -69.27049785055885, -74.10620847168758, 0.0],
    'P4':         [-74.10620847168758, -22.19441718187838, -88.53508496756277,
                   -69.27049785055884, -74.10620847168758, -180.0],
    'P5':         [-63.41392174214573, -23.452600702069333, -86.65404121903774,
                   -69.89335807889292, -63.41392174214573, -180.0],
    'J_LAND(迟到落点)': [-63.41, -13.45, -66.65, -69.89, -63.41, 0.0],
}

def fan(pose):
    f = Pose_2_Fanuc(pose)
    return '[%8.2f %8.2f %8.2f | %7.2f %7.2f %7.2f]' % tuple(f)

print('=== 各关节构型的 TCP(FK*tool) 与 法兰(FK) 的 Fanuc 值 ===')
poses = {}
for name, joints in J.items():
    fl = robot.SolveFK(joints)
    tcp = fl * tool
    poses[name] = (fl, tcp)
    print('%-16s TCP %s' % (name, fan(tcp)))
    print('%-16s 法兰 %s' % ('', fan(fl)))

records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json', encoding='utf-8'))
print('\n=== 轨迹源 11 录入点（TCP 值）===')
rec_poses = []
for k, rec in enumerate(records, 1):
    p = Fanuc_2_Pose(rec['values'])
    rec_poses.append(p)
    print('录入%2d: [%8.2f %8.2f %8.2f | %7.2f %7.2f %7.2f] singular=%s j6_delta=%s'
          % (k, *rec['values'], rec.get('singular'), rec.get('j6_delta')))

print('\n=== J_LAND 的 TCP 对每个录入点的位姿差（0=就是该点）===')
_, tcp_land = poses['J_LAND(迟到落点)']
for k, p in enumerate(rec_poses, 1):
    d = tcp_land * invH(p)
    print('录入%2d: 位置差=%9.3f mm  姿态差=%8.3f°' % (k, norm(d.Pos()), pose_angle(d) * 57.29578))

print('\n=== J_LAND 的【法兰】对 P9 的 TCP/法兰 等候选（复核）===')
fl_land = poses['J_LAND(迟到落点)'][0]
cands = {
    'FK(P9)': poses['P9(目标)'][0],
    'FK(P9)*tool': poses['P9(目标)'][1],
    'FK(P8)*tool': poses['P8(起点)'][1],
    'FK(P4)*tool': poses['P4'][1],
}
for name, c in cands.items():
    d = fl_land * invH(c)
    print('%-14s: 位置差=%9.3f mm  姿态差=%8.3f°' % (name, norm(d.Pos()), pose_angle(d) * 57.29578))

print('\n=== 反向：P9 的 TCP 对每个录入点（定位 P9 属于哪一步）===')
_, tcp9 = poses['P9(目标)']
for k, p in enumerate(rec_poses, 1):
    d = tcp9 * invH(p)
    if norm(d.Pos()) < 50 and pose_angle(d) * 57.29578 < 5:
        print('录入%2d: 位置差=%9.3f mm  姿态差=%8.3f°  ← 接近' % (k, norm(d.Pos()), pose_angle(d) * 57.29578))
print('（只列位置<50mm且姿态<5°的；全部结果从略）')
for k, p in enumerate(rec_poses, 1):
    d = tcp9 * invH(p)
    print('录入%2d: pos=%9.3f mm rot=%8.3f°' % (k, norm(d.Pos()), pose_angle(d) * 57.29578))
