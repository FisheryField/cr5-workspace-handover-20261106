#!/usr/bin/env python3
"""探针5：窗口级截图验证 Trace 颜色随工具色。
用 user32 找 RoboDK 主窗口，PrintWindow 截客户区。"""
import ctypes
import time
from ctypes import wintypes

from robodk.robolink import *  # noqa: F401,F403

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
psapi = ctypes.windll.psapi


def find_rdk_hwnd():
    result = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if "RoboDK" in buf.value and user32.IsWindowVisible(hwnd):
            result.append((hwnd, buf.value, cls.value))
        return True

    user32.EnumWindows(cb, 0)
    return result


wins = find_rdk_hwnd()
print("RoboDK 窗口:", wins)
# 优先真正的 RoboDK 3D 主窗（Qt 窗口类），排除脚本自己的 Tk 控制窗
qt = [w for w in wins if w[2].startswith("Qt")]
if not qt:
    raise SystemExit("找不到 RoboDK 主窗口（Qt）")
hwnd = qt[0][0]
print("目标窗口:", qt[0][1])


def shot(path):
    import PIL.Image as Image
    class RECT(ctypes.Structure):
        _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]
    rect = RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.r - rect.l, rect.b - rect.t
    hdc = user32.GetDC(hwnd)
    memdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(memdc, bmp)
    user32.SetProcessDPIAware()
    res = user32.PrintWindow(hwnd, memdc, 2)  # PW_RENDERFULLCONTENT
    bmpinfo = gdi32.GetObjectW(bmp, 0, None)
    class BMIH(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                    ("biPlanes", ctypes.c_short), ("biBitCount", ctypes.c_short), ("biCompression", ctypes.c_uint32),
                    ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
                    ("biClrUsed", ctypes.c_uint32), ("biClrImportant", ctypes.c_uint32)]
    hdr = BMIH()
    hdr.biSize = ctypes.sizeof(BMIH)
    hdr.biWidth, hdr.biHeight, hdr.biPlanes = w, -h, 1
    hdr.biBitCount = 32
    hdr.biCompression = 0
    class BMI(ctypes.Structure):
        _fields_ = [("bmiHeader", BMIH), ("ctypes_padding", ctypes.c_byte * 4)]
    bmi = BMI()
    bmi.bmiHeader = hdr
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf.raw, "raw", "BGRA", 0, 1)
    img.convert("RGB").save(path)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(hwnd, hdc)
    return path


RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tools = RDK.ItemList(ITEM_TYPE_TOOL)
tool = tools[0]
saved_j = robot.Joints().list()[:6]

def wiggle():
    q = saved_j[:]
    q[0] += 6.0
    robot.MoveJ(q)
    q[0] -= 6.0
    robot.MoveJ(q)
    time.sleep(0.3)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")

tool.setColor([1, 1, 0, 1])
wiggle()
shot("_trace_A_yellow.png")
print("A 完成")

RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
tool.setColor([1, 0, 1, 1])
wiggle()
shot("_trace_B_magenta.png")
print("B 完成")

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复完成:", [round(v, 2) for v in robot.Joints().list()[:6]])
