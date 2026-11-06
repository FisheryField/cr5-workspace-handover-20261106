#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make the TCP trajectory display RoboDK's default yellow, then verify by
counting pixels in a 3D snapshot (before vs after).

Safe/reversible: the original colour of every changed item is written to
data/robodk/trace_colors_before.txt so it can be restored with
setColor(<that value>).
"""
import io
import os
import sys
from collections import Counter

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)
YELLOW = [1.0, 1.0, 0.0, 1.0]

RDK = Robolink()
station = RDK.ActiveStation()


def describe(path):
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).reshape(-1, 3).astype(int)
    r, g, b = a[:, 0], a[:, 1], a[:, 2]
    out = {}
    out["yellow"] = int(((r > 170) & (g > 170) & (b < 120)).sum())
    out["red"] = int(((r > 150) & (g < 90) & (b < 90)).sum())
    out["green"] = int(((g > 140) & (r < 140) & (b < 140)).sum())
    out["blue"] = int(((b > 150) & (r < 130) & (g < 160)).sum())
    out["_pixels"] = len(a)
    return out


def snapshot(tag):
    p = os.path.join(OUT, "snap_%s.png" % tag)
    RDK.Render(True)
    RDK.Cam2D_Snapshot(p, None)
    return p, describe(p)


print("=== items (name / type / visible / colour) ===")
lines = []
points_items = []
for it in station.Childs():
    name = it.Name()
    try:
        vis = it.Visible()
    except Exception:  # noqa: BLE001
        vis = "?"
    col = None
    if it.Type() in (5, 9, 10):  # Object / Curve / Points
        try:
            col = list(it.Color())
        except Exception:  # noqa: BLE001
            col = None
    lines.append("%-46s type=%-3d visible=%s color=%s" % (name, it.Type(), vis, col))
    if it.Type() == 10:  # Points
        points_items.append((it, name, col, vis))
    print(lines[-1].encode("unicode_escape").decode("ascii"))

with io.open(os.path.join(OUT, "station_items.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

p_before, h_before = snapshot("colour_before")
print("\nbefore:", h_before)

print("\n=== recolour TCP* point items to yellow ===")
backup = []
for it, name, col, vis in points_items:
    if not name.upper().startswith("TCP"):
        print("   skip (not TCP):", name.encode("unicode_escape").decode("ascii"))
        continue
    backup.append((name, col))
    try:
        it.setColor(YELLOW)
        print("   %-46s %s -> [1,1,0,1]"
              % (name.encode("unicode_escape").decode("ascii"), col))
    except Exception as e:  # noqa: BLE001
        print("   %-46s setColor EXC %s"
              % (name.encode("unicode_escape").decode("ascii"), e))

with io.open(os.path.join(OUT, "trace_colors_before.txt"), "w", encoding="utf-8") as f:
    for name, col in backup:
        f.write("%s\t%s\n" % (name, col))

p_after, h_after = snapshot("colour_after")
print("\nafter :", h_after)
print("\ndelta :", {k: h_after[k] - h_before[k] for k in h_before if not k.startswith("_")})
print("backup: data/robodk/trace_colors_before.txt")
