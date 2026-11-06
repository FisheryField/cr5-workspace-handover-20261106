# -*- coding: utf-8 -*-
"""只读：测试 RoboDK API 是否被模态框阻塞（15s 内打印结果即为通）。"""
import sys, io, socket
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
socket.setdefaulttimeout(12)
try:
    from robodk import robolink
    RDK = robolink.Robolink()
    print('API 应答正常。RoboDK 版本:', RDK.Version())
    robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
    if robot.Valid():
        print('机器人当前模型关节:', [round(v, 2) for v in robot.Joints().list()[:6]])
        print('PoseTool:', robot.PoseTool().Pos())
    else:
        print('未找到机器人 item')
except Exception as e:
    print('API 阻塞/异常 (%s): %s' % (type(e).__name__, e))
print('DONE')
