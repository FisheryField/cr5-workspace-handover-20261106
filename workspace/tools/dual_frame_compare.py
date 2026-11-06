#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双参考系量化对照（只读，不需要使能）：
   源① API GetAngle()          （控制器上报 / 0x6062 系）
   源② 30005 包 q_target@128   （同包内的目标）
   源③ 30005 包 q_actual@32    （驱动器实际）
   源④ 30004 包 qActual@432    （RoboDK 脚本用的那个源）
   并交叉验证：②vs④ 应一致（正例自检）"""
import re
import socket
import struct
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
NAMES = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']


def packet(port, n=1440, timeout=6.0):
    s = socket.create_connection((HOST, port), timeout=timeout)
    s.settimeout(timeout)
    buf = b''
    while len(buf) < n:
        c = s.recv(4096)
        if not c:
            break
        buf += c
    s.close()
    return buf[:n]


def api(cmd, wait=0.9):
    s = socket.create_connection((HOST, 30003), timeout=8)
    s.settimeout(6)
    s.sendall((cmd + '\n').encode())
    time.sleep(wait)
    d = s.recv(8192).decode('utf-8', 'replace')
    s.close()
    return d.strip().replace('\n', ' ')


def get_api_angle():
    d = api('GetAngle()')
    m = re.search(r'\{([-0-9.,\s]+)\}', d)
    return [float(x) for x in m.group(1).split(',')] if m else None


def dbg6(off, blob):
    return list(struct.unpack_from('<6d', blob, off))


print('=== 采集（同一瞬间）===')
p5a = packet(30005)
t = time.time()
p5b = packet(30005)
p4 = packet(30004)
ang = get_api_angle()
print('  30005 读了两包（间隔 %.2fs）用于自检；30004 一包；API GetAngle 一次' % (t - t))

# 30005: q_actual@32, q_target@128, next@224  （工作区 read_joints.py 验证过的布局）
a5_act = dbg6(32, p5b)
a5_tgt = dbg6(128, p5b)
a5_next = dbg6(224, p5b)
# 30004: mode@24, qActual@432  （RoboDK 脚本的布局；mode 必须等于 API 的 RobotMode）
mode4 = struct.unpack_from('<Q', p4, 24)[0]
a4_act = dbg6(432, p4)
q5_act2 = dbg6(32, p5a)

print('')
print('=== 结果 ===')
print('  30004 robotMode = %d' % mode4)
hdr = '  %-3s | %14s | %14s | %14s | %14s | %12s' % (
    '轴', 'API GetAngle', '30005 q_target', '30005 q_actual', '30004 qActual', 'Δ(target−actual)')
print(hdr)
print('  ' + '-' * 100)
for i, n in enumerate(NAMES):
    d = a5_tgt[i] - a5_act[i]
    print('  %-3s | %+14.6f | %+14.6f | %+14.6f | %+14.6f | %+12.6f'
          % (n, ang[i] if ang else float('nan'), a5_tgt[i], a5_act[i], a4_act[i], d))

print('')
print('=== 正例自检（解码器是否可信）===')
same = max(abs(x - y) for x, y in zip(a5_act, a4_act))
print('  ① 30005 q_actual  vs 30004 qActual : 最大差 %.6f°  %s' % (same, '✓ 两解码器一致' if same < 0.01 else '✗ 不一致，需查'))
s2 = max(abs(x - y) for x, y in zip(q5_act2, a5_act))
print('  ② 30005 两包之间的 q_actual     : 最大差 %.6f°  %s' % (s2, '✓ 静止' if s2 < 0.01 else '手臂在动'))
if ang:
    s3 = max(abs(x - y) for x, y in zip(ang, a5_tgt))
    print('  ③ API 角度         vs q_target  : 最大差 %.6f°  %s' % (s3, '✓ 同系' if s3 < 0.05 else '✗ 不同系'))
    s4 = max(abs(x - y) for x, y in zip(ang, a5_act))
    print('  ④ API 角度         vs q_actual  : 最大差 %.6f°  ← ★双参考系差' % s4)
print('')
print('=== 控制器自己的视角（日志 PoseTrace 最近一组）===')
import subprocess  # noqa: E402
r = subprocess.run([r'C:\Users\FisheryField\AppData\Local\Temp\rq.cmd',
                    "grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' "
                    "/dobot/userdata/CR5_sys_files/project/logs/all/log | tail -3 | cut -c1-200"],
                   capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
print(r.stdout.strip() or '  (无)')
