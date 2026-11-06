#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Offline geometric analysis: handle mesh (flange frame) vs wheel disc.
# Wheel model (station-verified): center axis along X at (y=-956, z=300),
# R=180, slab x in [-20,20]. Orientation fixed (-90,0,-90):
#   base = TCP + (vz-159.629, -vx, vy)   for flange-frame vertex (vx,vy,vz)
# Step 1: bar geometry + validation against known probe results.
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

V = json.load(open(r"D:\mydata\glm-workplace\tools\handle_flange.json", encoding="utf-8"))["flange_verts"]
TCPZ = 159.629

# --- bar (short end) geometry ---
bar = [v for v in V if v[0] > 40.0]
stem = [v for v in V if v[0] <= 40.0]
t_bar = min(v[2] for v in bar)
print("verts total %d | bar(vx>40) %d | stem %d" % (len(V), len(bar), len(stem)))
print("bar: vx[%.2f,%.2f] vy[%.2f,%.2f] vz[%.2f,%.3f] -> thickness(t)=%.2f"
      % (min(v[0] for v in bar), max(v[0] for v in bar),
         min(v[1] for v in bar), max(v[1] for v in bar),
         t_bar, max(v[2] for v in bar), 159.629 - t_bar))
print("stem: vx[%.2f,%.2f] vz[%.2f,%.2f]" % (min(v[0] for v in stem), max(v[0] for v in stem),
      min(v[2] for v in stem), max(v[2] for v in stem)))

# rounded tip? distribution of vx among top 6mm
tipzone = sorted(set(round(v[0], 1) for v in bar if v[0] > 101))
print("tip vx levels (last 7mm):", tipzone)

# --- wheel test: inside disc volume -> (depth, r) ---
def wheel_test(p):
    x, y, z = p
    r = math.hypot(y + 956.0, z - 300.0)
    if abs(x) < 20.0 and r < 180.0:
        return (min(180.0 - r, 20.0 - abs(x)), r)
    return None

def evaluate(TCP):
    px, py, pz = TCP
    pen = []
    for v in V:
        p = (px + v[2] - TCPZ, py - v[0], pz + v[1])
        w = wheel_test(p)
        if w is not None:
            pen.append((v, w[0]))
    return pen

print("\n=== validation against known probe results ===")
for TCP, expect in (((30, -750, 300), "probe: 8/8 CLEAN"),
                    ((0, -750, 300), "probe: has sols, collides wheel"),
                    ((189.63, -750, 300), "user manual pose now: visually clear"),
                    ((-30, -750, 300), "probe: no IK sols")):
    pen = evaluate(TCP)
    if pen:
        dmax = max(d for _, d in pen)
        vxr = (min(v[0] for v, _ in pen), max(v[0] for v, _ in pen))
        print("TCP(%7.2f,%8.2f,%5.1f): %3d verts inside wheel, depth max %.2f, vx range [%.1f,%.1f]  <- %s"
              % (*TCP, len(pen), dmax, vxr[0], vxr[1], expect))
    else:
        print("TCP(%7.2f,%8.2f,%5.1f): handle CLEAR of wheel  <- %s" % (*TCP, expect))
