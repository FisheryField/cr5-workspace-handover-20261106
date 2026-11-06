#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag14: pull CollisionActivePairList with an extended receive timeout.
# If the map holds thousands of OFF entries -> root cause. Count + grep.
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
import robodk.robolink as rl

RDK = rl.Robolink(args='- timeout pass through default port')  # placeholder, replaced below
RDK = rl.Robolink()
# bump receive timeout for the big list transfer
try:
    RDK.TIMEOUT_REC = 120
    RDK._TIMEOUT_REC = 120
except Exception:
    pass
print("pulling CollisionActivePairList (may take up to 2 min)...")
t0 = time.time()
try:
    lst = RDK.CollisionActivePairList()
    dt = time.time() - t0
    print("entries: %d   (%.1f s)" % (len(lst), dt))
    states = {}
    wheel_pairs = []
    for a, b, st, sid in lst:
        states[st] = states.get(st, 0) + 1
        try:
            na, nb = a.Name(), b.Name()
            if '磨砂' in na or '磨砂' in nb:
                wheel_pairs.append((na, nb, st, sid))
        except Exception:
            pass
    print("state histogram:", states)
    print("pairs involving wheel:", len(wheel_pairs))
    for na, nb, st, sid in wheel_pairs[:40]:
        print("   %-30s <-> %-30s state=%s id=%s" % (na[:30], nb[:30], st, sid))
except Exception as e:
    print("FAILED after %.1f s: %s: %s" % (time.time()-t0, type(e).__name__, e))
