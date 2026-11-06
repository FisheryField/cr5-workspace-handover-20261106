# -*- coding: utf-8 -*-
"""只读：把手网格面分析（修正版，按站内手术变换）。
站内门把手_bs1 = handle_rod_182_v2.stl，GeometryPose=Fanuc_2_Pose([0,0,159.5,-90,0,0])：
  x_tool = x_stl;  y_tool = z_stl;  z_tool = 159.5 - y_stl（尖端 z=182、法兰端 z=0）。
红框面 = 把手平板的大侧面（STL 法向 ±Z ⇒ 工具系法向 ±Y）。
输出：该面的工具系方程 + 面贴圆柱侧面工作点 W=(0,-772,380) 的 TCP 姿态/位置。"""
import sys, io, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STL = r'D:\mydata\glm-workplace\tools\handle_rod_182_v2.stl'
data = open(STL, 'rb').read()
n_tri = struct.unpack_from('<I', data, 80)[0]
tris = []
off = 84
for _ in range(n_tri):
    v = struct.unpack_from('<12f', data, off)
    tris.append((v[3:6], v[6:9], v[9:12], v[0:3]))
    off += 50

def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def nrm(a): return math.sqrt(dot(a, a))

def stl2tool(p):
    return (p[0], p[2], 159.5 - p[1])

# 平板大面：|n_stl_z|>0.9
faces = {}
for (a, b, c, n) in tris:
    ln = nrm(n)
    if ln < 1e-9:
        continue
    n = (n[0]/ln, n[1]/ln, n[2]/ln)
    if abs(n[2]) < 0.9:
        continue
    if n[2] < 0:
        n = (-n[0], -n[1], -n[2])
    d = dot(n, a)   # = z_stl 平面
    key = round(d, 1)
    cr = cross(sub(b, a), sub(c, a))
    area = 0.5 * nrm(cr)
    e = faces.setdefault(key, {'area': 0.0, 'pts': []})
    e['area'] += area
    e['pts'].extend([a, b, c])

print('=== 把手平板大侧面（|n_z|>0.9）===')
for d, v in sorted(faces.items(), key=lambda kv: -kv[1]['area']):
    pts = [stl2tool(p) for p in v['pts']]
    zs = [p[2] for p in pts]; xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    print('面 z_stl=%.1f (→ 工具系 y_tool=%+.1f, 法向 y_tool=%+.1f)  面积=%.0f mm²' % (
        d, d, 1.0 if d > 0 else -1.0, v['area']))
    print('   工具系范围: x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]' % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

# 取面积最大面（红框侧），给出两种朝向解（法向朝 −Y 压圆柱）
big_d, big = max(faces.items(), key=lambda kv: kv[1]['area'])
side = 1.0 if big_d > 0 else -1.0     # 该面工具系: y_tool = side*big_d, 外法向 n_t=(0, side, 0)
print('\n红框面（取最大）: 工具系方程 y_tool = %+.2f, 外法向 n_tool=(0,%+.0f,0)' % (side*big_d, side))

# 姿态解：R·n_t=(0,-1,0) 且 ẑ→(0,0,-1)（TCP 竖直向下）
# n_t=(0,side,0)：若 side=+1 → ŷ'=(0,-1,0)? R·(0,1,0)=(0,-1,0) ⇒ ŷ_world=(0,-1,0)
#                 x̂ = ŷ×ẑ = (0,-1,0)×(0,0,-1) = ((-1)(-1)-0, 0-0, 0-0) = (1,0,0)
# 若 side=-1 → R·(0,-1,0)=(0,-1,0) ⇒ ŷ_world=(0,1,0); x̂=(0,1,0)×(0,0,-1)=(-1,0,0)
if side > 0:
    xw, yw, zw = (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)
else:
    xw, yw, zw = (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)

# RoboDK Mat 行主：行 i = 世界第 i 分量在工具轴上的系数 → m[i][j] = (xw,yw,zw)[i][j]
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
to_fanuc = ns['pose_to_fanuc_values']
from_fanuc = ns['fanuc_values_to_pose']
from robodk.robomath import Mat

m = Mat(4, 4)
axes = (xw, yw, zw)
for i in range(3):
    for j in range(3):
        m[i, j] = axes[j][i]
fan = [float(v) for v in to_fanuc(m)[:6]]
print('TCP 姿态 Fanuc [rx,ry,rz] = [%.2f, %.2f, %.2f]' % (fan[3], fan[4], fan[5]))

# 校验：R·n_t
back = from_fanuc(0, 0, 0, fan[3], fan[4], fan[5])
nt = (0.0, float(side), 0.0)
rn = tuple(sum(back[i][j] if hasattr(back[i], '__getitem__') else 0 for j in range(3)) for i in range(3))
# 直接用 Mat 元素
rn = (back[0,0]*nt[0]+back[0,1]*nt[1]+back[0,2]*nt[2],
      back[1,0]*nt[0]+back[1,1]*nt[1]+back[1,2]*nt[2],
      back[2,0]*nt[0]+back[2,1]*nt[1]+back[2,2]*nt[2])
print('校验 R·n_tool = (%.3f,%.3f,%.3f)  应为 (0,-1,0)' % rn)

# 接触：W=(0,-772,380)，n_world=(0,-1,0)，面 y_tool=side*big_d
# 面上点: n_t·x_tool = side*big_d? 方程 y_tool=side*big_d 且外法向 (0,side,0) ⇒ n_t·x=side*big_d=d_t
d_t = side * big_d
# n_w·TCP = n_w·W - d_t ⇒ -TCP_y = -W_y - d_t ⇒ TCP_y = W_y + d_t
W = (0.0, -772.0, 380.0)
TCP = (W[0], W[1] + d_t, W[2])
print('\n=== 接触解（面与圆柱侧面工作点 W=(0,-772,380) 相切）===')
print('  TCP 位置 = (%.2f, %.2f, %.2f)' % TCP)
print('  TCP 姿态 = rx=%.2f°  ry=%.2f°  rz=%.2f°' % (fan[3], fan[4], fan[5]))
print('  （J6 绕工具 z 自由；本解下工具 x 指向世界%s，L 弯臂沿工具 +x 伸出即朝世界%s，天然离开圆柱）'
      % ('+X' if xw[0] > 0 else '-X', '+X' if xw[0] > 0 else '-X'))
print('DONE')
