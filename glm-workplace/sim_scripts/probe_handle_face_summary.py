# -*- coding: utf-8 -*-
"""只读汇总：把手红框候选面（工具系 ±Y 法向的面族）→ 压向圆柱工作点 W=(0,-772,380)
所需的 TCP 姿态与位置。站内变换：x_tool=x_stl, y_tool=z_stl, z_tool=159.5-y_stl。"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\mydata\glm-workplace\sim_scripts')
from robodk.robomath import Mat

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
to_fanuc = ns['pose_to_fanuc_values']

W = (0.0, -772.0, 380.0)   # 圆柱侧面工作点（朝基座、中高）

# 候选面：(说明, y_tool 平面, 外法向 y 分量 s, 面积, z范围)
faces = [
    ('安装座薄侧面',      2.9,  +1, 486,  (122.4, 179.3)),
    ('安装座薄侧面(对侧)', -2.9, -1, 486,  (122.4, 179.3)),
    ('杆/主体大侧面',     10.8, +1, 1339, (3.5, 182.0)),
    ('杆/主体大侧面(对侧)', -10.8, -1, 1339, (3.5, 182.0)),
    ('外壳最外侧面',      12.3, +1, 605,  (0.0, 180.7)),
    ('外壳最外侧面(对侧)', -12.3, -1, 605,  (0.0, 180.7)),
]

def pose_for(s):
    # R·(0,s,0)=(0,-1,0) 且 ẑ→(0,0,-1)
    yw = (0.0, -1.0*s, 0.0)          # ŷ_world = R·(0,1,0) = -s*(0,-1,0)= (0,s,0)?? 直接解：
    # 需要 R·(0,s,0)=(0,-1,0) ⇒ R·(0,1,0)=(0,-s,0)
    yw = (0.0, -float(s), 0.0)
    zw = (0.0, 0.0, -1.0)
    xw = (yw[1]*zw[2]-yw[2]*zw[1], yw[2]*zw[0]-yw[0]*zw[2], yw[0]*zw[1]-yw[1]*zw[0])  # ŷ×ẑ
    m = Mat(4, 4)
    axes = (xw, yw, zw)
    for i in range(3):
        for j in range(3):
            m[i, j] = axes[j][i]
    fan = [float(v) for v in to_fanuc(m)[:6]]
    return xw, fan

print('工作点 W = (%.0f, %.0f, %.0f)   （圆柱 R150 中心 y=-922 ⇒ 朝基座表面 y=-772）\n' % W)
print('%-18s %8s %6s %8s   %-22s %s' % ('候选面', 'y_tool', '面积', 'TCP_y', 'TCP姿态 rx,ry,rz', '工具x指向'))
for name, y0, s, area, zr in faces:
    xw, fan = pose_for(s)
    tcp_y = W[1] + (s * y0 if False else (y0 if s > 0 else y0))
    # 面方程 n·x=d: n=(0,s,0), 平面 y=y0 ⇒ d=s*y0; TCP_y=W_y+d
    d = s * y0
    tcp_y = W[1] + d
    print('%-18s %+7.1f %5.0f   %+8.2f   [%7.2f, %6.2f, %6.2f]   世界%s' % (
        name, y0, area, tcp_y, fan[3], fan[4], fan[5],
        '+X' if xw[0] > 0 else '-X'))

print('\n要点：')
print('1) 所有候选面法向都在工具系 ±Y ⇒ TCP 必须竖直向下（ẑ→世界−Z）。')
print('2) 姿态只有两种等价解：rx=180,ry=0,rz=0（+Y 法向面族，与现轨迹 P8+ 相同）')
print('   或 rx=180,ry=0,rz=180（−Y 法向面族，等价 ry=180）。')
print('3) TCP y = 工作点y + 面偏移（上表）；x、z 对准工作点。J6/弯臂方向按需微调。')
print('DONE')
