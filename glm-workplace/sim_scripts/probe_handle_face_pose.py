# -*- coding: utf-8 -*-
"""只读：解析把手网格 handle_rod_182_v2.stl（=站内门把手_bs1，工具坐标系：
法兰 z=0、TCP/尖端 z=182）。找红框面（矩形块大侧面，⊥杆轴）→ 给出面法向/位置，
并计算面压向圆柱侧面工作点所需的 TCP 姿态与位置。纯标准库实现。"""
import sys, io, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robomath import Mat

STL = r'D:\mydata\glm-workplace\tools\handle_rod_182_v2.stl'
data = open(STL, 'rb').read()
n_tri = struct.unpack_from('<I', data, 80)[0]
print('三角形数 =', n_tri)

tris = []
off = 84
for _ in range(n_tri):
    vals = struct.unpack_from('<12f', data, off)
    tris.append((vals[3:6], vals[6:9], vals[9:12], vals[0:3]))
    off += 50

xs = [v[0] for t in tris for v in t[:3]]
ys = [v[1] for t in tris for v in t[:3]]
zs = [v[2] for t in tris for v in t[:3]]
print('顶点包围盒: X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]' % (
    min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def dot(a, b):
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def norm(a):
    return math.sqrt(dot(a, a))

faces = {}
for (a, b, c, n) in tris:
    ln = norm(n)
    if ln < 1e-9:
        continue
    n = (n[0]/ln, n[1]/ln, n[2]/ln)
    if n[2] < -0.5:
        n = (-n[0], -n[1], -n[2])
    d = dot(n, a)
    key = (round(n[0], 2), round(n[1], 2), round(n[2], 2), round(d, 1))
    cr = cross(sub(b, a), sub(c, a))
    area = 0.5 * norm(cr)
    e = faces.setdefault(key, {'area': 0.0, 'n': n, 'd': d, 'cx': 0.0, 'cy': 0.0, 'cz': 0.0, 'cnt': 0})
    e['area'] += area
    for p in (a, b, c):
        e['cx'] += p[0]; e['cy'] += p[1]; e['cz'] += p[2]
    e['cnt'] += 3

print('\n=== ⊥杆轴(n_z≈0)且面积最大的平面簇（候选=红框面） ===')
cands = [(k, v) for k, v in faces.items() if abs(k[2]) < 0.05 and v['area'] > 50]
cands.sort(key=lambda kv: -kv[1]['area'])
for k, v in cands[:6]:
    print('法向 n=(%.2f,%.2f,%.2f)  d=%.2f  面积=%.1f mm²  质心=(%.1f,%.1f,%.1f)' % (
        v['n'][0], v['n'][1], v['n'][2], v['d'], v['area'],
        v['cx']/v['cnt'], v['cy']/v['cnt'], v['cz']/v['cnt']))

key, face = cands[0]
n_t = face['n']
d_t = face['d']
print('\n选定红框面: n_tool=(%.3f,%.3f,%.3f), d=%.3f (面方程 n·x = d)' % (n_t[0], n_t[1], n_t[2], d_t))

# 目标旋转：R·n_t=(0,-1,0)（面法向压向圆柱）；ẑ'=(0,0,-1)（TCP 竖直向下）
x2 = (0.0, -1.0, 0.0)          # x̂'  = 面法向目标
z2 = (0.0, 0.0, -1.0)          # ẑ'  = 向下
y2 = cross(z2, x2)
R = (x2, y2, z2)               # 行=世界向量按工具轴分量? 列式：R·v = v0*x2+v1*y2+v2*z2
print('旋转构造: x̂→(0,-1,0), ẑ→(0,0,-1), ŷ→(%.0f,%.0f,%.0f)' % y2)

def apply(R, v):
    return (v[0]*R[0][0] + v[1]*R[1][0] + v[2]*R[2][0],
            v[0]*R[0][1] + v[1]*R[1][1] + v[2]*R[2][1],
            v[0]*R[0][2] + v[1]*R[1][2] + v[2]*R[2][2])

rn = apply(R, n_t)
print('R·n_t = (%.4f,%.4f,%.4f)  (目标 (0,-1,0))' % rn)

# 转 Fanuc 角：宏头 fanuc 对
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
to_fanuc = ns['pose_to_fanuc_values']
from_fanuc = ns['fanuc_values_to_pose']

m = Mat(4, 4)
for i in range(3):
    for j in range(3):
        m[i, j] = R[j][i]      # RoboDK Mat 行主：R[i][j]=第i工具轴世界像的第j分量
fan = [float(v) for v in to_fanuc(m)[:6]]
print('TCP 姿态 Fanuc [rx,ry,rz] = [%.3f, %.3f, %.3f]' % (fan[3], fan[4], fan[5]))

back = from_fanuc(0, 0, 0, fan[3], fan[4], fan[5])
Rb = [[back[i, j] for j in range(3)] for i in range(3)]
rn2 = apply(Rb, n_t)
print('往返校验 R·n_t = (%.4f,%.4f,%.4f)' % rn2)

# 接触位置：W=(0,-772,380)（圆柱朝基座侧面中高），n_world=(0,-1,0)
W = (0.0, -772.0, 380.0)
TCP = (W[0], W[1] + d_t, W[2])
print('\n=== 面贴圆柱工作点 W=(0,-772,380) 的接触解 ===')
print('  TCP 位置 = (%.2f, %.2f, %.2f)' % TCP)
print('  TCP 姿态 = rx=%.2f°  ry=%.2f°  rz=%.2f°' % (fan[3], fan[4], fan[5]))
print('  J6 绕工具 z 自由 → 用它把 L 弯臂转离圆柱体（建议弯臂朝世界 +X 或 -X 侧倾）')

# 对照：现轨迹 rx=180 时该面法向的世界方向
R180 = ((1, 0, 0), (0, -1, 0), (0, 0, -1))
print('\n对照 rx=180（现轨迹）时面法向世界方向 = (%.2f,%.2f,%.2f)' % apply(R180, n_t))
R90 = ((1, 0, 0), (0, 0, -1), (0, 1, 0))
print('对照 rx=90  时面法向世界方向 = (%.2f,%.2f,%.2f)' % apply(R90, n_t))
print('DONE')
