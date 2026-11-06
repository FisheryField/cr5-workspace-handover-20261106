#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# read-only: what tool offset is active on the robot right now
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
tool = robot.getLink(robolink.ITEM_TYPE_TOOL)
print("active tool item:", repr(tool.Name()) if tool.Valid() else "(none)")
print("PoseTool():\n", robot.PoseTool())
handle = RDK.Item("门把手_bs1")
print("门把手_bs1 relative to flange:\n", handle.PoseAbs() * robot.PoseAbs().inv() if handle.Valid() and robot.Valid() else "(n/a)")
