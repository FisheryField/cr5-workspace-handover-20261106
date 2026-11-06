#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多次标零取最优（目标：把六轴 |gActual| 压到 ≤0.03°，争取 0.011° 级）。

前提：主控 = 原版（8416cf0e…）、机器人已使能、手臂完全静止。
逻辑：标零一次 → 读 gActual → 若最大偏差 > TARGET 且未满 3 次 ⇒ 再标一次。
每次标零都会重新采样瞬间位置，故多次有概率取到更好的。
"""
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
RSH = [r'C:\Program Files\PyManager\python.exe', r'D:\mydata\workspace\tools\rssh.py']
D = '/dobot/userdata/CR5_sys_files/project/logs/all'
STOCK = '8416cf0eee070a640702c077eb904b4e'
TARGET = 0.03         # 达标阈值（°）
MAX_TRIES = 3


def rq(cmd, t=90):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True, timeout=t,
                       encoding='utf-8', errors='replace', stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


def read_actual():
    """取最新一条 PoseTrace 的 gActualPosition（必须是 PoseTrace，不是 FollowError）"""
    txt = rq("grep -a 'PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -1" % D)
    m = re.search(r'gActualPosition:\s*([-\d.,]+)', txt)
    if not m:
        return None
    try:
        return [float(v) for v in m.group(1).split(',')][:6]
    except ValueError:
        return None


def wait_done(max_s=40):
    for i in range(int(max_s / 2)):
        time.sleep(2)
        out = rq("grep -a 'servo calihome done' %s/log 2>/dev/null | tail -1" % D)
        if 'servo calihome done' in out:
            return True
    return False


print('=== 0) 前置检查 ===')
app = rq("md5sum /dobot/userdata/codesys/allST/Application.app").split(' ')[0].strip()
print('  主控 :', app, '✓' if app == STOCK else '✗ 不是原版！')
if app != STOCK:
    print('  !! 必须原版才能标零，退出')
    sys.exit(1)
en = rq("grep -a 'robot enabled\\|robot disabled' %s/log 2>/dev/null | tail -1 | cut -c1-120" % D)
print('  使能 :', en.strip() or '(未读到)')
fw = rq("grep -a 'settVersion#5132' %s/log 2>/dev/null | tail -1 | cut -c1-110" % D)
print('  固件 :', fw.strip())
cur = read_actual()
print('  标零前 gActual :', cur)

best = None
best_try = 0
for k in range(1, MAX_TRIES + 1):
    print('')
    print('=== 第 %d 次标零 ===' % k)
    try:
        req = urllib.request.Request('http://%s:22000/calibrate/home' % HOST, data=b'{}',
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=40) as r:
            print('  POST  →  HTTP %s  %s' % (r.status, r.read().decode('utf-8', 'replace')[:80]))
    except Exception as e:  # noqa: BLE001
        print('  POST 异常: %s: %s' % (type(e).__name__, e))
        break
    ok = wait_done(40)
    print('  结果  :', '★ servo calihome done ✓' if ok else '✗ 未见 done（40s）')
    if not ok:
        print(rq("grep -a 'HomeNumdone\\|servo calihome' %s/log 2>/dev/null | tail -6 | cut -c1-140" % D).rstrip())
        break
    a = read_actual()
    if a is None:
        print('  读 gActual 失败')
        continue
    mx = max(abs(v) for v in a)
    print('  gActual: %s' % ', '.join('%+.6f' % v for v in a))
    print('  最大偏差: %.6f°  %s' % (mx, '★ 达标 ✓' if mx <= TARGET else '（> %.3f°，可再试一次）' % TARGET))
    if best is None or mx < best[0]:
        best = (mx, a[:], k)
    if mx <= TARGET:
        break
    time.sleep(3)          # 让它稳定一下再标第二次

print('')
print('=== 汇总 ===')
if best:
    print('  最优：第 %d 次，最大偏差 %.6f°' % (best[2], best[0]))
    print('  六轴：%s' % ', '.join('%+.6f' % v for v in best[1]))
    print('  达标：%s' % ('✓ 已到 %.3f° 以内' % TARGET if best[0] <= TARGET else '✗ 仍在 %.6f°（3.1.5.0 的实测下限约 0.011°）' % best[0]))
else:
    print('  未取得有效结果')
print('')
print('=== 现在三列 ===')
print(rq("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' %s/log 2>/dev/null | tail -3 | cut -c1-200" % D).rstrip())
