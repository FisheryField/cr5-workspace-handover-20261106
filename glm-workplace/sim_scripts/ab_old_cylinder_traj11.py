# -*- coding: utf-8 -*-
"""A/B 相位1：把站内圆柱临时还原为【旧环境】wheel_R180_H40 @ (0,-956,300)（含碰撞对重建），
离线跑站内 TCP仿真 的轨迹11 规划；无论成败，finally 里恢复 v14w6 环境（R150×H50 @ y=-926）。
目的：判定轨迹11 失败是否由【新圆柱环境】引起（挡板对已证无关）。"""
import sys, io, json, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, RUNMODE_SIMULATE, ITEM_TYPE_ROBOT, ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

CYL = '磨砂圆柱_R180_H40'
BASE = 'Dobot CR5 Base'
OLD_STL = r'D:\mydata\glm-workplace\tools\wheel_R180_H40.stl'
NEW_STL = r'D:\mydata\glm-workplace\tools\cylinder_R150_H50.stl'
OLD_FANUC = [0.0, -956.0, 300.0, 90.0, -0.0, 90.0]
NEW_FANUC = [0.0, -926.0, 300.0, 90.0, -0.0, 90.0]

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
base = RDK.Item(BASE)
assert robot.Valid() and base.Valid()

def replace_cylinder(stl, fanuc_vals, label):
    old = RDK.Item(CYL, ITEM_TYPE_OBJECT)
    if old.Valid():
        old.Delete()
    item = RDK.AddFile(stl)
    item.setParent(base)
    item.setPose(Fanuc_2_Pose(list(fanuc_vals)))
    item.setName(CYL)
    item.setVisible(True)
    # 重建碰撞对（镜像 _enable_obstacle_checks 对圆柱的处理）
    for link in range(1, 7):
        RDK.setCollisionActivePair(1, robot, item, link, 0)
    for tool in RDK.ItemList(ITEM_TYPE_TOOL):
        RDK.setCollisionActivePair(1, tool, item)
    print('[环境] 圆柱已替换为 %s @ y=%.0f' % (label, fanuc_vals[1]))

def disable_baffle_pairs():
    baf = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
    if not baf.Valid():
        return
    for link in range(1, 7):
        RDK.setCollisionActivePair(0, robot, baf, link, 0)
    for tool in RDK.ItemList(ITEM_TYPE_TOOL):
        RDK.setCollisionActivePair(0, tool, baf)

result = 'ABORT'
try:
    replace_cylinder(OLD_STL, OLD_FANUC, '旧 R180×H40')
    disable_baffle_pairs()

    SRC = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump\tcpsim_20261014_094115\TCP仿真_station.py'
    code = open(SRC, encoding='utf-8').read()
    lines = [l for l in code.splitlines() if l.strip() != 'root.mainloop()']
    ns = {}
    exec(compile('\n'.join(lines), 'TCP仿真_station', 'exec'), ns)
    records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹11.json', encoding='utf-8'))
    records = ns['_retreat_orientation_records'](records)
    ns['robot'].setJoints([0.0] * 6)
    RDK.setRunMode(RUNMODE_SIMULATE)
    last = []
    def log(m):
        last.append(str(m))
    try:
        plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
        result = 'PASS(%d段)' % len(plan)
        print('RESULT: 旧环境下预检通过：', len(plan), '段')
    except Exception as e:
        result = 'FAIL'
        print('RESULT: 旧环境下仍失败:', type(e).__name__, str(e)[:220])
        cyl_hits = [m for m in last if '磨砂圆柱' in m]
        print('含圆柱碰撞的日志条数:', len(cyl_hits))
        for m in last[-3:]:
            print('  最后:', m[:200])
finally:
    replace_cylinder(NEW_STL, NEW_FANUC, '恢复 R150×H50')
    print('环境已恢复 v14w6（R150×H50 @ y=-926）；判定 =', result)
