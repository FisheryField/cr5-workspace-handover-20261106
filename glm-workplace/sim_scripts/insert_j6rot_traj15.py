# -*- coding: utf-8 -*-
"""轨迹15 手术：P14 与 P15 之间插入 3 点 = (20,-707,380,90,0,90) 的 J6+90/180/270。
步骤：算 Fanuc 角 → IK 验证 → 备份 → 插入 → 结构自检。"""
import sys, io, json, math, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robomath import invH

PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹15.json'

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
fanuc_to_pose = ns['fanuc_values_to_pose']
pose_to_fanuc = ns['pose_to_fanuc_values']
from robodk import robolink
from robodk.robomath import rotz
RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

base = fanuc_to_pose(20.0, -707.0, 380.0, 90.0, 0.0, 90.0)
new_points = []
for d in (90.0, 180.0, 270.0):
    T = base * rotz(d)          # 绕工具 z 旋转 = J6 旋转
    fan = [float(v) for v in pose_to_fanuc(T)[:6]]
    name = 'J6+%g°' % d
    # IK 验证（用当前工具 182）
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    print('%s -> Fanuc=(%.3f, %.3f, %.3f, %.3f, %.3f, %.3f)  IK=%s' % (
        name, fan[0], fan[1], fan[2], fan[3], fan[4], fan[5],
        ('%d解' % len(s)) if s else '无解!!'))
    if not s:
        raise SystemExit('%s 不可达，中止插入' % name)
    new_points.append({
        'type': 'TCP',
        'values': [round(v, 6) for v in fan],
        'singular': False,
        'j6_delta': 0,
    })

records = json.load(open(PATH, encoding='utf-8'))
print('\n原点数 =', len(records))
assert len(records) >= 15
p14 = records[13]
print('P14 =', p14['values'])
print('P15 =', records[14]['values'])

ts = time.strftime('%Y%m%d-%H%M')
bak = PATH.replace('.json', '_pre_J6rot_%s.json.bak' % ts)
shutil.copy2(PATH, bak)
print('备份 =', bak)

records = records[:14] + new_points + records[14:]
out = json.dumps(records, indent=2, ensure_ascii=False) + '\n'
open(PATH, 'w', encoding='utf-8').write(out)

chk = json.load(open(PATH, encoding='utf-8'))
assert len(chk) == 22 + 3
assert chk[13]['values'] == json.loads(json.dumps(p14['values']))
print('插入后点数 =', len(chk))
for k in range(14, 17):
    print('新 P%d = %s' % (k + 1, chk[k]['values']))
print('DONE：已插入 3 点（现共 25 点）')
