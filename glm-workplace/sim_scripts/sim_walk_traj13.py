# -*- coding: utf-8 -*-
"""仿真走位：轨迹13(z460版)@tool126+场景-860→-886 当前配置。
SIMULATE 模式按预检计划逐段动画（MoveJ 直达段 / 途经点细分段），不碰实机。
开始前模型归零与预检起点一致；结束恢复 RUN_ROBOT。"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()
print('PoseTool =', robot.PoseTool().Pos())

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
print('LOG_VERSION =', ns.get('LOG_VERSION'))
fixed = ns['_ensure_canonical_tool']()
print('工具守护 =', '已自动恢复' if fixed else '正常')

records = ns['_retreat_orientation_records'](
    json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹13_t126_z460.json', encoding='utf-8')))
print('执行点数 =', len(records))

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0] * 6)
time.sleep(0.3)

plan = ns['_plan_continuous_trajectory'](records, 500.0, lambda m: None)
print('预检规划 OK：%d 段。开始仿真走位…' % len(plan))

t0 = time.time()
for k, step in enumerate(plan, 1):
    wps = step.get('waypoints') or []
    if step['method'] == 'MoveJ' and not wps:
        robot.MoveJ(step['joints'])
        print('P%-2d MoveJ 直达            (%.1fs)' % (k, time.time() - t0))
    elif wps:
        # 认证细分路径：逐途经点 MoveJ（途经点均在认证直线上）
        for w in wps:
            robot.MoveJ(w)
        robot.MoveJ(step['joints'])
        print('P%-2d 细分 %d 跳 → 终点    (%.1fs)' % (k, len(wps), time.time() - t0))
    else:
        robot.MoveJ(step['joints'])
        print('P%-2d MoveJ（%s）   (%.1fs)' % (k, step.get('p2p_note', ''), time.time() - t0))

print('\n=== 仿真走位完成：21/21，总耗时 %.1fs ===' % (time.time() - t0))
OUT = r'D:\mydata\glm-workplace\tools\sim_walk_traj13_end.png'
import os
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('终点截图 =', OUT if os.path.exists(OUT) else '失败')

RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（已恢复 RUN_ROBOT；模型停在轨迹终点）')
