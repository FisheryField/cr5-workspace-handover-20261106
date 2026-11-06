# -*- coding: utf-8 -*-
"""站内平移：磨砂圆柱_R150_H50 与 挡板_半封闭3面 整体 +z 170mm（17cm）。
只改位姿平移的 z 分量（旋转/几何/名字/父级不动），幂等保护：已在目标值则跳过。
不保存工作站。代码/宏场景注释按用户要求暂不改（后面集中修改）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT

DELTA = 170.0
TARGETS = {          # 当前基座系 z（探针实测）→ 预期目标 z
    '磨砂圆柱_R150_H50': (300.0, 470.0),
    '挡板_半封闭3面': (0.0, 170.0),
}

RDK = Robolink()
all_ok = True
for name, (z_old, z_new) in TARGETS.items():
    it = RDK.Item(name, ITEM_TYPE_OBJECT)
    assert it.Valid(), '未找到 ' + name
    P = it.Pose()
    z0 = P[2, 3]
    print('%s：z %.3f -> ?' % (name, z0))
    if abs(z0 - z_new) < 1e-6:
        print('  已在目标 z=%.1f，跳过（幂等）' % z_new)
        continue
    if abs(z0 - z_old) > 1e-6:
        print('  注意：当前 z=%.3f 非预期原值 %.1f，按相对 +170 执行' % (z0, z_old))
    orig = {(i, j): P[i, j] for i in range(4) for j in range(4)}
    P[2, 3] = z0 + DELTA
    it.setPose(P)
    Q = it.Pose()
    ok_z = abs(Q[2, 3] - (z0 + DELTA)) < 1e-9
    ok_rest = all(abs(Q[i, j] - v) < 1e-9 for (i, j), v in orig.items() if (i, j) != (2, 3))
    print('  新位姿 z = %.3f（Δ=%+.3f）  z校验=%s  xy/旋转不变=%s' % (Q[2, 3], Q[2, 3] - z0, ok_z, ok_rest))
    if not (ok_z and ok_rest):
        all_ok = False

print('--- 平移后位姿（基座系平移） ---')
for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    it = RDK.Item(name, ITEM_TYPE_OBJECT)
    if it.Valid():
        P = it.Pose()
        print('  %s: t=(%.3f, %.3f, %.3f)' % (name, P[0, 3], P[1, 3], P[2, 3]))
print('ALL_OK =', all_ok, '（未保存工作站）')
