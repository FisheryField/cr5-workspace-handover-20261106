# -*- coding: utf-8 -*-
"""恢复 PoseTool=[0,0,100]（v14w17 守护语义；连接同步把它清零了），重摆接触位形，复核+截图+留驻。"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')

print('PoseTool 现值 Fanuc =', ['%.3f' % v for v in Pose_2_Fanuc(robot.PoseTool())])
robot.setPoseTool(Pose(0, 0, 100, 0, 0, 0))
print('已恢复 PoseTool Fanuc =', ['%.3f' % v for v in Pose_2_Fanuc(robot.PoseTool())])

P = cyl.Pose(); P[1, 3] = -915.0; cyl.setPose(P)
for link in range(0, 7):
    RDK.setCollisionActivePair(COLLISION_ON, robot, cyl, link, 0)
if handle.Valid():
    RDK.setCollisionActivePair(COLLISION_ON, handle, cyl)
RDK.setCollisionActive(COLLISION_ON)

robot.setJoints([75.8, 106.1, -81.8, -24.3, -75.8, 0.0])
tcp = robot.SolveFK(robot.Joints()) * robot.PoseTool()
f = Pose_2_Fanuc(tcp)
print('TCP 实测 xyz=(%.2f, %.2f, %.2f) Fanuc=(%.1f, %.1f, %.1f)' % (f[0], f[1], f[2], f[3], f[4], f[5]))
print('碰撞 robot=%s handle=%s' % (robot.Collision(cyl), handle.Collision(cyl) if handle.Valid() else None))

RDK.Render(True)
time.sleep(2.0)
SHOT = r'D:\mydata\glm-workplace\tools\rdk_contact_final.png'
if os.path.exists(SHOT): os.remove(SHOT)
r = RDK.Cam2D_Snapshot(SHOT, None)
print('截图 ret=%r size=%d' % (r, os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
print('DONE（圆柱 y=-915；PoseTool 已恢复；臂留驻；未保存工作站）')
