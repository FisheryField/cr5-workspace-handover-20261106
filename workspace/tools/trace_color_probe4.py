#!/usr/bin/env python3
"""探针4：Trace 曲线颜色控制。
步骤：
  1) 记录关节、Trace On
  2) 工具设黄 -> 运动 -> 截图 A（_trace_A_yellow.png）
  3) Trace Reset 后工具设洋红 -> 运动 -> 截图 B（_trace_B_magenta.png）
  4) 恢复：Trace Off/Reset、关节恢复、删除截图副本之外的一切变动
图像对比两段曲线颜色即可判定「trace 颜色是否随工具色」。
"""
import time

from robodk.robolink import *  # noqa: F401,F403

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tools = RDK.ItemList(ITEM_TYPE_TOOL)
print("工具 items:", [str(t) for t in tools])
tool = tools[0]  # ItemList 返回的就是可用 item
print("tool:", tool.Name(), "type ok:", tool.Valid())

saved_j = robot.Joints().list()[:6]

def wiggle(tag):
    q = saved_j[:]
    q[0] += 6.0
    robot.MoveJ(q)
    q[0] -= 6.0
    robot.MoveJ(q)
    time.sleep(0.3)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")

tool.setColor([1, 1, 0, 1])  # 黄
wiggle("yellow")
import subprocess
subprocess.run(["powershell", "-c", "Add-Type -AssemblyName System.Windows.Forms;"
                 "[System.Windows.Forms.Screen]::PrimaryScreen;"], capture_output=True)
# 截图用 Cam2D_Snapshot 不可靠，改用 .NET CopyFromScreen（主屏全图）
import ctypes
from ctypes import wintypes
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
import PIL.ImageGrab as grab  # 本机有 Pillow
grab.grab().save("_trace_A_yellow.png")
print("A 截图完成")

RDK.Command("Trace", "Reset")  # 清掉黄色段
RDK.Command("Trace", "On")
tool.setColor([1, 0, 1, 1])   # 洋红
wiggle("magenta")
grab.grab().save("_trace_B_magenta.png")
print("B 截图完成")

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("完成；关节恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
