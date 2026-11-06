#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn the RoboDK trace ON, snapshot the 3D view and describe its colours.

Used to determine objectively what the TCP trace currently looks like
(RoboDK's default trace is a yellow curve).
"""
import os
import sys
from collections import Counter

sys.path.insert(0, r"D:\software\RoboDK\Python")
from robodk.robolink import Robolink  # noqa: E402

OUT = r"D:\mydata\workspace\data\robodk"
os.makedirs(OUT, exist_ok=True)

for mod in ("PIL", "numpy", "matplotlib", "cv2"):
    try:
        __import__(mod)
        print("lib %-11s OK" % mod)
    except Exception as e:  # noqa: BLE001
        print("lib %-11s MISSING (%s)" % (mod, type(e).__name__))

RDK = Robolink()
print("trace on  ->", RDK.Command("Trace", "On"))
try:
    RDK.Render(True)
except Exception:  # noqa: BLE001
    pass

tag = sys.argv[1] if len(sys.argv) > 1 else "on"
path = os.path.join(OUT, "snap_%s.png" % tag)
print("snapshot  ->", RDK.Cam2D_Snapshot(path, None), path,
      os.path.getsize(path) if os.path.exists(path) else 0)

try:
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).reshape(-1, 3).astype(int)
    print("image:", im.size, "pixels:", len(a))

    def mask(name, fn):
        m = fn(a[:, 0], a[:, 1], a[:, 2])
        n = int(m.sum())
        print("   %-22s %8d px  (%.3f%%)" % (name, n, 100.0 * n / len(a)))
        return n

    mask("yellow (R>170,G>170,B<120)", lambda r, g, b: (r > 170) & (g > 170) & (b < 120))
    mask("orange-ish", lambda r, g, b: (r > 180) & (g > 90) & (g < 190) & (b < 110))
    mask("red", lambda r, g, b: (r > 150) & (g < 90) & (b < 90))
    mask("green", lambda r, g, b: (g > 140) & (r < 140) & (b < 140))
    mask("blue", lambda r, g, b: (b > 150) & (r < 130) & (g < 160))
    mask("cyan", lambda r, g, b: (b > 150) & (g > 150) & (r < 130))
    mask("white/bright", lambda r, g, b: (r > 230) & (g > 230) & (b > 230))

    q = (a // 32 * 32)
    cnt = Counter(map(tuple, q[::7]))
    print("   top colour buckets (32-step quantised):")
    for c, n in cnt.most_common(12):
        print("      RGB~%-16s %6d" % (str(c), n))
except Exception as e:  # noqa: BLE001
    print("analysis failed:", type(e).__name__, e)

print("trace off ->", RDK.Command("Trace", "Off"))
