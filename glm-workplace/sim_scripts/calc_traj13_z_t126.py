# -*- coding: utf-8 -*-
"""tool=126 下求轨迹13 高点排(z=470,rx=180)的可达 z 上限：
逐点降 z 找 IK 可解边界 → 取全排最紧的 → 留 5mm 余量取整到 5mm 网格。
生成临时副本（原版不动）→ 整段预检 → 报结果。恢复182 由外部负责。"""
import sys, io, json, math, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
print('PoseTool =', robot.PoseTool().Pos())

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
fanuc_to_pose = ns['fanuc_values_to_pose']

records = json.load(open(SRC, encoding='utf-8'))
hi = [(k, r) for k, r in enumerate(records)
      if r['type'] == 'TCP' and abs(float(r['values'][2]) - 470.0) < 1e-6]
print('高点排(z=470) =', ['P%d' % (k + 1) for k, _ in hi])

def ik_ok(k, z):
    v = [float(x) for x in records[k]['values'][:6]]
    v[2] = z
    T = fanuc_to_pose(*v)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    return len(s) > 0

limits = {}
for k, _ in hi:
    z = 470.0
    while z >= 380.0:
        if ik_ok(k, z):
            break
        z -= 1.0
    limits[k] = z
    print('  P%-2d 最高可达 z ≈ %.0f' % (k + 1, z))

z_max = min(limits.values())
z_final = math.floor((z_max - 5.0) / 5.0) * 5.0
print('\n全排最紧边界 = %.0f  ⇒ 统一取 z = %.0f（留 ≥5mm 余量，5mm 网格）' % (z_max, z_final))

# 生成临时副本：只降高点排
out = copy.deepcopy(records)
for k, _ in hi:
    out[k]['values'][2] = z_final
TMP = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13_t126_z%d.json' % int(z_final)
open(TMP, 'w', encoding='utf-8').write(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
print('临时副本 =', TMP, '（原版未动）')

# 整段预检
records2 = ns['_retreat_orientation_records'](out)
robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
def log(m):
    print('  |', m)
try:
    plan = ns['_plan_continuous_trajectory'](records2, 500.0, log)
    print('\n=== 预检通过：%d 段 ===' % len(plan))
    print('RESULT: PASS')
except ValueError as exc:
    print('\n=== 预检失败 ===')
    print(' ', exc)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
