#!/usr/bin/env python3
"""探针34：验证最终集成方案——独立 API 连接后台采样 TCP + AddCurve 画黄线。
与主脚本同构的函数写法（函数属性存状态，避免类/模块常量——AST 提取器只认函数）。
主线程做 MoveJ 摆动（模拟执行期），采样线程并行记录，最后画线+截图差分验黄。
"""
import ctypes
import os
import threading
import time

import ctypes.wintypes as wt
from PIL import Image
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL


def _tcp_curve_start():
    state = {'stop': threading.Event(), 'thread': None, 'points': [], 'error': None}

    def _sample_loop():
        try:
            rdk2 = Robolink()
            robot2 = rdk2.Item('', ITEM_TYPE_ROBOT)
            tool2 = robot2.getLink(ITEM_TYPE_TOOL)
            if not tool2.Valid():
                state['error'] = '未找到工具，轨迹采样未启动'
                return
            state['points'].append(list(tool2.PoseAbs().Pos()))
            while not state['stop'].is_set():
                state['points'].append(list(tool2.PoseAbs().Pos()))
                state['stop'].wait(0.05)
        except Exception as exc:
            state['error'] = '%s: %s' % (type(exc).__name__, exc)

    t = threading.Thread(target=_sample_loop, daemon=True)
    state['thread'] = t
    _tcp_curve_start.state = state
    t.start()


def _tcp_curve_stop_and_draw():
    state = getattr(_tcp_curve_start, 'state', None)
    _tcp_curve_start.state = None
    if not state:
        return None
    state['stop'].set()
    if state['thread'] is not None:
        state['thread'].join(timeout=2.0)
    return state


# --- 窗口保持非最小化（否则快照冻结）---
user32 = ctypes.windll.user32
rows = []
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def cb(h, l):
    rows.append(h)
    return True


user32.EnumWindows(WNDENUMPROC(cb), 0)
for h in rows:
    b = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(h, b, 256)
    if "RoboDK - 不受限制" in b.value and user32.IsIconic(h):
        user32.ShowWindow(h, 9)
        time.sleep(1.0)
print("窗口已确认非最小化")

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
RDK.Render(True)
saved = robot.Joints().list()[:6]

RDK.Command('Trace', 'Off')
RDK.Command('Trace', 'Reset')
_tcp_curve_start()
t0 = time.perf_counter()
for d in (12.0, -12.0, 10.0, -10.0):
    q = list(saved)
    q[0] += d
    robot.MoveJ(q)
dur = time.perf_counter() - t0
state = _tcp_curve_stop_and_draw()
print("采样错误:", state['error'])
pts = state['points']
print("运动耗时 %.1fs, 采样 %d 点 (~%.0f Hz)" % (dur, len(pts), len(pts) / dur if dur else 0))
seg = [((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** .5 for a, b in zip(pts, pts[1:])]
print("相邻点距 mm: min %.1f max %.1f" % (min(seg), max(seg)))

from robodk import robomath
curve = RDK.AddCurve(robomath.Mat([list(p) for p in pts]).tr(), None, False, 0)
curve.setName("_probe34_黄轨迹")
curve.setColorCurve([1.0, 0.82, 0.0, 1.0])
print("curve:", curve.Name(), curve.Valid())

A = os.path.abspath("_probe34_A.png")
RDK.Command("Snapshot", A)
curve.Delete()
B = os.path.abspath("_probe34_B.png")
RDK.Command("Snapshot", B)

ia, ib = Image.open(A).convert("RGB"), Image.open(B).convert("RGB")
w, h = ia.size
pa, pb = ia.load(), ib.load()
diff = [(x, y) for y in range(h) for x in range(w) if pa[x, y] != pb[x, y]]
n = len(diff)
yellow = sum(1 for x, y in diff if pa[x, y][0] > 170 and pa[x, y][1] > 120 and pa[x, y][2] < 110)
print("曲线建/删 diff px=%d 黄色系=%d" % (n, yellow))
robot.setJoints(saved)
print("关节复原:", [round(v, 2) for v in robot.Joints().list()[:6]])
