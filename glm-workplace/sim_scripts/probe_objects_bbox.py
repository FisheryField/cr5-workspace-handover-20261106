# -*- coding: utf-8 -*-
# 只读：站内物体清单 + 门把手_bs1 当前网格包围盒/位姿
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT, ITEM_TYPE_ROBOT
from robodk.robomath import Pose_2_Fanuc

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
print('robot:', robot.Name(), 'PoseTool=', ['%.3f' % v for v in Pose_2_Fanuc(robot.PoseTool())])

for it in RDK.ItemList(filter=ITEM_TYPE_OBJECT):
    try:
        bb = it.BoundingBox()
        # bb: Min/Max
        mn = bb.min if hasattr(bb, 'min') else None
        print('OBJ %-24s parent=%-16s' % (it.Name(), it.Parent().Name() if it.Parent().Valid() else '-'))
        try:
            mnv = [round(v, 1) for v in bb.minlist()]
            mxv = [round(v, 1) for v in bb.maxlist()]
            print('     bbox min=%s max=%s' % (mnv, mxv))
        except Exception as e:
            print('     bbox EXC', e)
        if it.Name() == '门把手_bs1':
            print('     pose =', ['%.3f' % v for v in Pose_2_Fanuc(it.Pose())])
            print('     geo  =', ['%.3f' % v for v in Pose_2_Fanuc(it.GeometryPose())])
    except Exception as exc:
        print('OBJ', it.Name(), 'EXC', exc)
