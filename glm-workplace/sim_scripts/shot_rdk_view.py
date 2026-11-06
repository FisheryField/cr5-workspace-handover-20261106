# -*- coding: utf-8 -*-
"""只读：截取 RoboDK 主 3D 视图当前画面（不改站、不保存工作站）。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink

OUT = r'D:\mydata\glm-workplace\tools\rdk_view_now.png'
if os.path.exists(OUT):
    os.remove(OUT)
RDK = Robolink()
err = None
for cam in (None, 0):
    try:
        r = RDK.Cam2D_Snapshot(OUT, cam)
        print('Cam2D_Snapshot(cam=%r) -> %r' % (cam, r))
        if os.path.exists(OUT) and os.path.getsize(OUT) > 0:
            print('OK', OUT, os.path.getsize(OUT), 'bytes')
            break
    except Exception as e:
        err = e
        print('cam=%r err: %s' % (cam, e))
else:
    raise SystemExit('截图失败: %r' % err)
