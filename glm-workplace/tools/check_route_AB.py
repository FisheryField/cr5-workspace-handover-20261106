#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# READ-ONLY: check poses A and B against the wheel (pure mesh math + SolveIK;
# no station mutation, robot stays parked). Also answers wheel R/H from mesh.
import sys, io, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl, rotx, roty, rotz

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

# ---------- wheel dimensions from mesh ----------
wd = open(r"D:\mydata\glm-workplace\tools\wheel_R180_H40.stl", "rb").read()
n = struct.unpack("<I", wd[80:84])[0]
wx, wy, wz, rad = [], [], [], []
off = 84
for i in range(n):
    v = struct.unpack("<12fH", wd[off:off+50]); off += 50
    for t in range(3):
        x, y, z = v[3+3*t], v[4+3*t], v[5+3*t]
        wx.append(x); wy.append(y); wz.append(z); rad.append(math.hypot(y, z))
print("WHEEL mesh: local z(轴向) [%.2f, %.2f] -> H=%.2f ; max radius=%.2f"
      % (min(wz), max(wz), max(wz)-min(wz), max(rad)))

# ---------- convention calibration against live parked pose ----------
live = robot.Pose()
lp = live.Pos()
print("\nparked flange live:", ["%.2f" % v for v in lp])
def zyx(x,y,z,rx,ry,rz): return transl(x,y,z)*rotz(math.radians(rz))*roty(math.radians(ry))*rotx(math.radians(rx))
def xyz(x,y,z,rx,ry,rz): return transl(x,y,z)*rotx(math.radians(rx))*roty(math.radians(ry))*rotz(math.radians(rz))
cand = {}
for name, fn in [("zyx(rotz*roty*rotx)", zyx), ("xyz(rotx*roty*rotz)", xyz)]:
    M = fn(24.0, -673.22, 300.0, -90, 0, -90)
    err = max(abs(M[i][j]-live[i][j]) for i in range(3) for j in range(4))
    cand[name] = (fn, err)
    print("  convention %-20s max err vs live: %.5f" % (name, err))
fn = min(cand, key=lambda k: cand[k][1]); POSE = cand[fn][0]
print("  -> using", fn)

# ---------- tool mesh ----------
td = open(r"D:\mydata\glm-workplace\tools\diag8_tool_local.stl", "rb").read()
n = struct.unpack("<I", td[80:84])[0]
verts = []
off = 84
for i in range(n):
    v = struct.unpack("<12fH", td[off:off+50]); off += 50
    for t in range(3):
        verts.append((v[3+3*t], v[4+3*t], v[5+3*t]))
gp = tool.GeometryPose()
PT = robot.PoseTool()
print("\ntool: %d STL verts, GeometryPose t=%s, PoseTool z=%.3f" %
      (len(verts), ["%.1f" % v for v in gp.Pos()], PT.Pos()[2]))

# ---------- wheel solids ----------
def test(verts_b, xc):
    inside = 0; maxd = 0.0; minc = 1e9
    for (x, y, z) in verts_b:
        if xc-20 <= x <= xc+20:
            r = math.hypot(y+956.0, z-300.0)
            if r <= 180.0:
                inside += 1; maxd = max(maxd, 180.0-r)
            else:
                minc = min(minc, r-180.0)
    return inside, maxd, (minc if minc < 1e8 else None)

def ik_check(x,y,z,rx,ry,rz):
    fl = POSE(x,y,z,rx,ry,rz)
    sols = robot.SolveIK(fl * PT)
    if not sols: return 0, None
    lo, hi = robot.JointLimits()
    ok = [s for s in (q.list()[:6] for q in ([sols[i] for i in range(sols.size(1))] if hasattr(sols,'size') else sols))
          if all(lo[k]-1e-6 <= ok_v <= hi[k]+1e-6 for k, ok_v in enumerate(q))]
    return len(sols.list()) if hasattr(sols,'list') else len(sols), (ok[0] if ok else None)

def report(tag, x,y,z,rx,ry,rz):
    fl = POSE(x,y,z,rx,ry,rz)
    T = fl * gp
    vb = [(T*x and ((T[:3,:3]*(vx,vy,vz))[0]+T[0][3], (T[:3,:3]*(vx,vy,vz))[1]+T[1][3], (T[:3,:3]*(vx,vy,vz))[2]+T[2][3])) for (vx,vy,vz) in []]
    # simpler: use homogeneous multiply
    import itertools
    vb = []
    Rm, pm = T[:3,:3], T.Pos()
    for (vx,vy,vz) in verts:
        vx2 = Rm[0][0]*vx+Rm[0][1]*vy+Rm[0][2]*vz+pm[0]
        vy2 = Rm[1][0]*vx+Rm[1][1]*vy+Rm[1][2]*vz+pm[1]
        vz2 = Rm[2][0]*vx+Rm[2][1]*vy+Rm[2][2]*vz+pm[2]
        vb.append((vx2,vy2,vz2))
    iN, dN, cN = test(vb, 179.665)
    iO, dO, cO = test(vb, 0.0)
    ns, q0 = ik_check(x,y,z,rx,ry,rz)
    mv = ""
    if q0:
        r = robot.MoveJ_Test(q0, q0)
        mv = "静态台/地:%s" % ("净" if r == 0 else "撞%d" % r)
    print("%-26s 新轮: 顶点入体 %4d  最深 %6.2f 间隙 %s | 旧轮位: 入体 %3d 最深 %5.2f | IK解 %d %s"
          % (tag, iN, dN, ("%.1f" % cN) if cN is not None else "-", iO, dO, ns, mv))

print("\n%-26s %s" % ("pose", "results"))
report("A (0,-562,500,180,0,180)", 0,-562,500,180,0,180)
report("B (40,-750,300,-90,0,-90)", 40,-750,300,-90,0,-90)
report("PARK(24,-673.22,300) sanity", 24,-673.22,300,-90,0,-90)
report("B'触碰 (40,-668.22,300)", 40,-668.22,300,-90,0,-90)
report("B'工作δ5 (40,-673.22,300)", 40,-673.22,300,-90,0,-90)
print("\n(joints untouched:", ["%.1f" % v for v in robot.Joints().list()[:6]], ")")
