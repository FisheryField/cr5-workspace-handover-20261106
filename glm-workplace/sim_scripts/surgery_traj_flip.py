# -*- coding: utf-8 -*-
"""轨迹手术：在 (90,0,0)→(180,0,0) 翻转对之间插入"退出→远距翻转"中间点，
把 47 途经点的姿态细分 MoveL 变成两段短 MoveJ（P6 死因消除）。
适用于 连续轨迹12/13（Δ=+76 版）。插入点 y=-630（距圆柱面 -700 有 70mm）。
"""
import json

FILES = [
    r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹12.json',
    r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json',
]
Y_MID = -630.0

for path in FILES:
    with open(path, 'r', encoding='utf-8') as f:
        pts = json.load(f)
    out = []
    n_ins = 0
    for i, p in enumerate(pts):
        out.append(p)
        v = p['values']
        # 找 (·,·,·,90,0,0) 且下一点是 (同x,·,·,180,0,0) 的翻转对
        if i + 1 < len(pts):
            v2 = pts[i + 1]['values']
            if (abs(v[3] - 90) < 1e-9 and abs(v[4]) < 1e-9 and abs(v[5]) < 1e-9
                    and abs(v2[3] - 180) < 1e-9 and abs(v2[4]) < 1e-9 and abs(v2[5]) < 1e-9
                    and abs(v2[0] - v[0]) < 1e-9):
                x = v[0]
                out.append({'type': 'TCP', 'values': [x, Y_MID, v[2], 90.0, 0.0, 0.0],
                            'singular': False, 'j6_delta': 0})
                out.append({'type': 'TCP', 'values': [x, Y_MID, v[2], 180.0, 0.0, 0.0],
                            'singular': False, 'j6_delta': 0})
                n_ins += 2
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('%s: %d 点 → %d 点（插入 %d）' % (path.split('\\')[-1], len(pts), len(out), n_ins))
    for i, p in enumerate(out):
        print('%2d %s' % (i, p['values']))
