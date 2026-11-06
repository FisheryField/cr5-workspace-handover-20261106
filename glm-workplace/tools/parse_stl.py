#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Offline: parse the two exported STLs, establish frames, locate the
# short-end tip. Pure local math, no RoboDK connection.
import sys, io, struct, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

def load_stl(path):
    data = open(path, "rb").read()
    tri = []
    if data[:5] == b"solid":
        # ASCII
        txt = data.decode("utf-8", "replace")
        verts, n = [], 0
        for line in txt.splitlines():
            ls = line.strip().split()
            if ls and ls[0] == "vertex":
                verts.append([float(ls[1]), float(ls[2]), float(ls[3])])
                if len(verts) == 3:
                    tri.append(verts); verts = []
    else:
        n = struct.unpack("<I", data[80:84])[0]
        off = 84
        for _ in range(n):
            rec = struct.unpack("<12fH", data[off:off+50])
            tri.append([list(rec[3:6]), list(rec[6:9]), list(rec[9:12])])
            off += 50
    return tri

def bbox(tri):
    vs = [v for t in tri for v in t]
    xs = [v[0] for v in vs]; ys = [v[1] for v in vs]; zs = [v[2] for v in vs]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)), vs

htri = load_stl(r"D:\mydata\glm-workplace\tools\handle_bs1.stl")
wtri = load_stl(r"D:\mydata\glm-workplace\tools\wheel_R180_H40.stl")
print("handle tris:", len(htri), " wheel tris:", len(wtri))

(hx0,hx1,hy0,hy1,hz0,hz1), hvs = bbox(htri)
print("handle STL bbox: x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (hx0,hx1,hy0,hy1,hz0,hz1))
(wx0,wx1,wy0,wy1,wz0,wz1), wvs = bbox(wtri)
print("wheel  STL bbox: x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (wx0,wx1,wy0,wy1,wz0,wz1))

# handle STL is presumably in tool OBJECT frame; transform to FLANGE frame:
# GeometryPose = transl(0,0,159.5) * rotX(-90):  [x,y,z]_obj -> (x, z_obj, -y_obj) + (0,0,159.5)
hf = [[v[0], v[2], -v[1] + 159.5] for v in hvs]
fx0 = min(v[0] for v in hf); fx1 = max(v[0] for v in hf)
fy0 = min(v[1] for v in hf); fy1 = max(v[1] for v in hf)
fz0 = min(v[2] for v in hf); fz1 = max(v[2] for v in hf)
print("handle FLANGE-frame bbox: x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (fx0,fx1,fy0,fy1,fz0,fz1))

# tip candidates: max flange-Z (furthest from flange along tool axis = TCP direction)
TCPZ = 159.629
zmax = max(v[2] for v in hf)
tips = [v for v in hf if v[2] > zmax - 0.5]
print("vertices within 0.5mm of max flange-Z (%.2f): %d" % (zmax, len(tips)))
if tips:
    tx = [v[0] for v in tips]; ty = [v[1] for v in tips]
    print("  tip cluster: x[%.2f,%.2f] y[%.2f,%.2f]" % (min(tx),max(tx),min(ty),max(ty)))

# distance from TCP point (0,0,159.629) to each vertex; report nearest & furthest
d = [math.dist(v, (0,0,TCPZ)) for v in hf]
imin, imax = d.index(min(d)), d.index(max(d))
print("closest vertex to TCP: (%.2f,%.2f,%.2f) d=%.2f" % (*hf[imin], d[imin]))
print("furthest vertex from TCP: (%.2f,%.2f,%.2f) d=%.2f" % (*hf[imax], d[imax]))

json.dump({"flange_verts": hf, "tcp_off": [0,0,TCPZ]},
          open(r"D:\mydata\glm-workplace\tools\handle_flange.json", "w", encoding="utf-8"))
print("saved handle_flange.json")
