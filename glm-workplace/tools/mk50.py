#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
src = io.open(r"tools\repro_traj7_sim.py", encoding="utf-8").read()
old = 'ns["_plan_continuous_trajectory"](expanded, 500.0, ns["log"])'
new = 'ns["_plan_continuous_trajectory"](expanded, 50.0, ns["log"])'
assert old in src
io.open(r"tools\repro_traj7_sim_50.py", "w", encoding="utf-8").write(src.replace(old, new))
print("ok")
