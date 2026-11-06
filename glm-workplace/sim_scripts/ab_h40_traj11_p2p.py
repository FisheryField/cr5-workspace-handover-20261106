# -*- coding: utf-8 -*-
"""确认实验：站内圆柱临时替换为 R150×H40 @ (0,-926,300)（长度回到40，位置不动），
跑 P2P 规划器的轨迹11 离线预检；finally 恢复 R150×H50 @ (0,-926,300)。
判定：若 PASS ⇒ P23 死因 = H40→H50 的 x 端条带（±5mm 新领地）。"""
import sys, io, json, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, RUNMODE_SIMULATE, ITEM_TYPE_ROBOT, ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL
from robodk.robomath import Fanuc_2_Pose

CYL = '磨砂圆柱_R180_H40'
BASE = 'Dobot CR5 Base'
STL_H40 = r'D:\mydata\glm-workplace\tools\cylinder_R150_H40.stl'
STL_H50 = r'D:\mydata\glm-workplace\tools\cylinder_R150_H50.stl'
FANUC = [0.0, -926.0, 300.0, 90.0, -0.0, 90.0]

def write_cyl(path, r, h, n=180):
    tris = []
    zt, zb = h / 2.0, -h / 2.0
    ring = [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        x1, y1 = ring[k]; x2, y2 = ring[(k + 1) % n]
        nx, ny = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        ln = math.hypot(nx, ny); nrm = (nx / ln, ny / ln, 0.0)
        tris.append((nrm, (x1, y1, zb), (x2, y2, zb), (x2, y2, zt)))
        tris.append((nrm, (x1, y1, zb), (x2, y2, zt), (x1, y1, zt)))
    for k in range(n):
        x1, y1 = ring[k]; x2, y2 = ring[(k + 1) % n]
        tris.append(((0.0, 0.0, 1.0), (0.0, 0.0, zt), (x1, y1, zt), (x2, y2, zt)))
        tris.append(((0.0, 0.0, -1.0), (0.0, 0.0, zb), (x2, y2, zb), (x1, y1, zb)))
    buf = bytearray(b'\x00' * 80 + struct.pack('<I', len(tris)))
    for nrm, a, b, c in tris:
        buf += struct.pack('<12fH', *nrm, *a, *b, *c, 0)
    open(path, 'wb').write(buf)

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
base = RDK.Item(BASE)
assert robot.Valid() and base.Valid()

def replace(stl, label):
    old = RDK.Item(CYL, ITEM_TYPE_OBJECT)
    if old.Valid():
        old.Delete()
    item = RDK.AddFile(stl)
    item.setParent(base)
    item.setPose(Fanuc_2_Pose(list(FANUC)))
    item.setName(CYL)
    item.setVisible(True)
    for link in range(1, 7):
        RDK.setCollisionActivePair(1, robot, item, link, 0)
    for tool in RDK.ItemList(ITEM_TYPE_TOOL):
        RDK.setCollisionActivePair(1, tool, item)
    print('[环境] 圆柱 =', label)

result = 'ABORT'
try:
    if not __import__('os').path.exists(STL_H40):
        write_cyl(STL_H40, 150.0, 40.0)
        print('已生成', STL_H40)
    replace(STL_H40, 'R150×H40 @ y=-926（实验组）')

    src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
    lines = src.splitlines()
    stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
    ns = {}
    exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
    records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹11.json', encoding='utf-8'))
    records = ns['_retreat_orientation_records'](records)
    robot.setJoints([0.0] * 6)
    RDK.setRunMode(RUNMODE_SIMULATE)
    def log(m):
        if '种子' in m or 'P23' in m or '预检' in m:
            print('  |', str(m)[:160])
    try:
        plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
        result = 'PASS(%d段)' % len(plan)
        print('RESULT: R150×H40 环境下轨迹11 预检通过：', len(plan), '段')
    except Exception as e:
        result = 'FAIL'
        print('RESULT: R150×H40 下仍失败:', type(e).__name__, str(e)[:220])
finally:
    replace(STL_H50, 'R150×H50 @ y=-926（恢复现环境）')
    print('环境已恢复；判定 =', result)
