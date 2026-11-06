# -*- coding: utf-8 -*-
"""y_mid 扫描：从轨迹7/11 原版重建 Δ=+76 + 翻转手术（插入 y=y_mid 的 90/180 翻转对），
用 v14w23 规划器验证 traj13，找第一个"无大细分 MoveL（途经点≤15）"的 y_mid，落盘两条轨迹。"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk import robolink

SRC7 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json'
SRC11 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹11.json'
OUT12 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹12.json'
OUT13 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
DELTA = 76.0

def build_at(src, y_mid):
    pts = json.load(open(src, encoding='utf-8'))
    outp = []
    for i, p in enumerate(pts):
        e = dict(p)
        v = [float(x) for x in p['values']]
        if abs(v[1]) > 1e-9:
            v[1] += DELTA
        v[2] += 170.0
        e['values'] = v
        outp.append(e)
        if i + 1 < len(pts):
            v2 = [float(x) for x in pts[i + 1]['values']]
            if abs(v2[1]) > 1e-9:
                v2[1] += DELTA
            v2[2] += 170.0
            if (abs(v[3] - 90) < 1e-9 and abs(v[4]) < 1e-9 and abs(v[5]) < 1e-9
                    and abs(v2[3] - 180) < 1e-9 and abs(v2[4]) < 1e-9 and abs(v2[5]) < 1e-9
                    and abs(v2[0] - v[0]) < 1e-9):
                x = v[0]
                outp.append({'type': 'TCP', 'values': [x, y_mid, v[2], 90.0, 0.0, 0.0],
                             'singular': False, 'j6_delta': 0})
                outp.append({'type': 'TCP', 'values': [x, y_mid, v[2], 180.0, 0.0, 0.0],
                             'singular': False, 'j6_delta': 0})
    return outp

# 载入规划器
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_macro_head', 'exec'), ns)
plan_fn = ns['_plan_continuous_trajectory']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def try_y(y_mid):
    data = build_at(SRC11, y_mid)
    json.dump(data, open(OUT13, 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
    records = ns['_retreat_orientation_records'](json.loads(json.dumps(data)))
    robot.setJoints([0.0] * 6)
    logs = []
    def log(m):
        logs.append(m)
    try:
        plan = plan_fn(records, 500.0, log)
    except ValueError as exc:
        return False, '预检失败: %s' % exc, logs
    big = []
    for m in logs:
        mt = re.search(r'直线细分（(\d+) 途经点）', m)
        if mt and int(mt.group(1)) > 15:
            big.append(m.strip())
    return (not big), ('仍有大细分: %d 段' % len(big) if big else '无大细分 MoveL ✓'), logs

best = None
for y in (-630.0, -560.0, -500.0, -440.0, -400.0, -360.0):
    ok, msg, logs = try_y(y)
    print('y_mid=%7.1f  %s' % (y, msg))
    for m in logs:
        if '细分' in m:
            print('    |', m.strip())
    if ok:
        best = y
        break
if best is None:
    print('=== 所有候选都有大细分，取最远 -360 落盘待人工判断 ===')
    best = -360.0
    try_y(best)

# 用 best 落盘两条
data13 = build_at(SRC11, best)
json.dump(data13, open(OUT13, 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
data12 = build_at(SRC7, best)
json.dump(data12, open(OUT12, 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
print('=== 落盘 y_mid=%.0f：轨迹12=%d 点 轨迹13=%d 点 ===' % (best, len(data12), len(data13)))
