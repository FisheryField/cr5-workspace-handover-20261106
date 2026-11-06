#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spatial analysis of a RoboDK 3D snapshot.

For each colour mask report: pixel count, bounding box, fill ratio and a coarse
"is it a thin long curve or a blob?" verdict.
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = r"D:\mydata\workspace\data\robodk"


def analyse(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    masks = {
        "red": (r - np.maximum(g, b) > 60) & (r > 110),
        "green": (g - np.maximum(r, b) > 50) & (g > 100),
        "blue": (b - np.maximum(r, g) > 50) & (b > 110),
        "yellow": (r > 160) & (g > 160) & (b < 120) & (abs(r - g) < 60),
        "cyan": (g > 140) & (b > 140) & (r < 130),
        "magenta": (r > 130) & (b > 130) & (g < 110),
    }
    print("=== %s  (%dx%d) ===" % (os.path.basename(path), w, h))
    for name, m in masks.items():
        n = int(m.sum())
        if n < 50:
            print("   %-8s %6d px" % (name, n))
            continue
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        fill = n / float(bw * bh)
        # count coarse cells (32x32) occupied -> measure of how "spread" it is
        cells = len({(int(x) // 32, int(y) // 32) for x, y in zip(xs[::11], ys[::11])})
        span = max(bw, bh)
        shape = ("thin long curve" if fill < 0.15 and span > 200
                 else "sparse/scattered" if fill < 0.25
                 else "solid blob/frame")
        print("   %-8s %6d px  bbox=%dx%d at (%d,%d)  fill=%.3f  cells=%d  -> %s"
              % (name, n, bw, bh, x0, y0, fill, cells, shape))
    print()


for f in sorted(os.listdir(OUT)):
    if f.startswith("snap_") and f.endswith(".png"):
        analyse(os.path.join(OUT, f))
