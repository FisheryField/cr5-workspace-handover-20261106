#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag5: is the wheel even in the collision-check item list of this station?
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

print("--- CollisionItems() (items considered for collision checking) ---")
items = RDK.CollisionItems()
if items:
    for it in items:
        try:
            print("  [%d] %s" % (it.type(), it.Name()))
        except Exception as e:
            print("  ?", e)
else:
    print("  EMPTY list!")

print("\n--- CollisionPairs() map summary ---")
pairs = RDK.CollisionPairs()
print("total pairs in map:", len(pairs) if pairs else 0)

print("\n--- pair states involving wheel or tool ---")
if pairs:
    for a, b, st, sid in pairs:
        try:
            na, nb = a.Name(), b.Name()
            if '磨砂' in na or '磨砂' in nb or '把手' in na or '把手' in nb:
                print("  %s <-> %s : state=%s" % (na, nb, st))
        except Exception:
            pass
